"""The first line in the whole update that executes something out of the bucket.

Everything before this point downloads and checks. This is the moment code from
the internet is run, and the tests here exist to hold one promise: it does not
happen unless both checks have passed in this run.

The guard is a record written inside `prepare` that no caller can set. An
ordering that depends on every caller remembering the order is not a safety
property, so it is not implemented as one.

What cannot be tested on this Mac: CREATE_NEW_CONSOLE, and a real Windows
console window surviving its parent. The one thing about detachment worth
proving rather than asserting is that a spawned child outlives the process that
started it, and that is proved here with a harmless child.
"""
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))

import packaging  # noqa: E402
import updates  # noqa: E402

from test_update_unpack import TOP, build_package, make_zip  # noqa: E402


def cleared_package(tmp_path):
    """A package that has been through both checks, the way prepare leaves it."""
    root = build_package(tmp_path)
    program = root / packaging.PROGRAM_DIR
    (program / "python" / "python.exe").write_text("binary\n", encoding="utf-8")
    (program / packaging.MANIFEST_NAME).write_text(
        packaging.build_manifest(program), encoding="utf-8")
    return root


@pytest.fixture(autouse=True)
def clean():
    updates.forget_cleared()
    updates.end_run()
    yield
    updates.forget_cleared()
    updates.end_run()


# --- nothing runs until both checks have passed -----------------------------
def test_a_package_that_was_not_checked_is_never_started(tmp_path):
    package = cleared_package(tmp_path)
    started = []
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.hand_off(package, spawn=lambda *a, **k: started.append(a))
    assert "was not checked" in refused.value.message
    assert not started


def test_clearing_one_package_does_not_clear_another(tmp_path):
    """The record names the exact package. A second tree on disk, however it
    got there, is not the one that passed."""
    good = cleared_package(tmp_path / "a")
    other = cleared_package(tmp_path / "b")
    updates._mark_cleared(good, "a" * 64)
    started = []
    with pytest.raises(updates.UpdateRefused):
        updates.hand_off(other, spawn=lambda *a, **k: started.append(a))
    assert not started


def test_the_record_cannot_survive_into_the_next_attempt(tmp_path, fake_bucket):
    """prepare forgets it first, so a run that fails half way cannot leave a
    package cleared behind it."""
    package = cleared_package(tmp_path)
    updates._mark_cleared(package, "a" * 64)
    with pytest.raises(updates.UpdateRefused):
        updates.prepare({"version": "0.5.4", "zip": "missing.zip", "size": 100})
    assert not updates._is_cleared(package)


# --- the command it runs ----------------------------------------------------
def test_it_runs_the_new_packages_python_and_the_new_packages_script(tmp_path):
    package = cleared_package(tmp_path)
    updates._mark_cleared(package, "a" * 64)
    seen = []
    command = updates.hand_off(package, spawn=lambda cmd, **kw: seen.append((cmd, kw)))
    inner = package / packaging.PROGRAM_DIR
    assert command == [str(inner / "python" / "python.exe"),
                       str(inner / "app" / "update_apply.py")]
    assert seen[0][0] == command


def test_it_never_runs_the_running_versions_copy_of_anything(tmp_path):
    """Once the handoff starts, nothing in the old version folder may be held
    open, because that is what leaves install_windows free to copy over it."""
    package = cleared_package(tmp_path)
    updates._mark_cleared(package, "a" * 64)
    command = updates.hand_off(package, spawn=lambda *a, **k: None)
    for part in command:
        assert str(package) in part


def test_a_package_missing_its_installer_is_refused(tmp_path):
    package = cleared_package(tmp_path)
    (package / packaging.PROGRAM_DIR / "app" / "update_apply.py").unlink()
    updates._mark_cleared(package, "a" * 64)
    started = []
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.hand_off(package, spawn=lambda *a, **k: started.append(a))
    assert "part that installs it" in refused.value.message
    assert not started


def test_a_package_missing_its_python_is_refused(tmp_path):
    package = cleared_package(tmp_path)
    (package / packaging.PROGRAM_DIR / "python" / "python.exe").unlink()
    updates._mark_cleared(package, "a" * 64)
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.hand_off(package, spawn=lambda *a, **k: None)
    assert "Python it needs" in refused.value.message


def test_a_spawn_that_fails_leaves_the_app_alive_and_says_so(tmp_path):
    package = cleared_package(tmp_path)
    updates._mark_cleared(package, "a" * 64)

    def cannot(*_a, **_k):
        raise OSError("no")

    with pytest.raises(updates.UpdateRefused) as refused:
        updates.hand_off(package, spawn=cannot)
    # What it can observe: this process is the one answering, so it is running.
    # Whether it "works" is not something it can see.
    assert "this app is still running" in refused.value.message
    assert "Nothing has changed" in refused.value.message


# --- the whole prepared run -------------------------------------------------
def test_prepare_downloads_checks_unpacks_and_clears(tmp_path, fake_bucket):
    import hashlib

    zip_path = make_zip(build_package(tmp_path), tmp_path / "package.zip")
    body = zip_path.read_bytes()
    name = "Roy R. Fisher v0.5.4.zip"
    fake_bucket.put(name, body)
    fake_bucket.put(name + ".sha256",
                    "%s  %s\n" % (hashlib.sha256(body).hexdigest(), name))

    package = updates.prepare({"version": "0.5.4", "zip": name, "size": len(body)})
    assert package.name == TOP
    assert updates._is_cleared(package)


def test_a_bad_hash_stops_before_anything_is_unpacked(tmp_path, fake_bucket):
    zip_path = make_zip(build_package(tmp_path), tmp_path / "package.zip")
    body = zip_path.read_bytes()
    name = "Roy R. Fisher v0.5.4.zip"
    fake_bucket.put(name, body)
    fake_bucket.put(name + ".sha256", "%s  %s\n" % ("b" * 64, name))

    with pytest.raises(updates.UpdateRefused):
        updates.prepare({"version": "0.5.4", "zip": name, "size": len(body)})
    assert not (updates.download_dir() / updates.UNPACKED_DIR).exists()
    assert not updates._is_cleared(updates.download_dir() / updates.UNPACKED_DIR / TOP)


# --- closing the app --------------------------------------------------------
def test_closing_clears_the_runtime_record_before_it_goes(tmp_path):
    import startup

    home = tmp_path / "0.5.3"
    (home / packaging.PROGRAM_DIR).mkdir(parents=True)
    startup.write_runtime(home, 51234, "0.5.3")
    assert startup.runtime_file(home).is_file()

    went = []
    updates.close_the_app(home, exit_now=lambda: went.append(True))
    assert not startup.runtime_file(home).is_file()
    assert went == [True], "it did not actually leave"


def test_a_runtime_record_that_will_not_go_does_not_stop_it_leaving(tmp_path,
                                                                    monkeypatch):
    """A missed tidy-up is already safe: the port it names answers nothing."""
    import startup

    monkeypatch.setattr(startup, "clear_runtime",
                        lambda _h: (_ for _ in ()).throw(OSError("locked")))
    went = []
    updates.close_the_app(tmp_path, exit_now=lambda: went.append(True))
    assert went == [True]


# --- detachment, the one part worth proving ---------------------------------
def test_a_spawned_child_outlives_the_process_that_started_it(tmp_path):
    """Asserted by doing it rather than by believing it. The Windows console
    flags cannot be tested here; that a child survives its parent can."""
    marker = tmp_path / "still-here.txt"
    script = tmp_path / "child.py"
    script.write_text(
        "import sys, time\n"
        "time.sleep(0.4)\n"
        "open(sys.argv[1], 'w').write('alive')\n", encoding="utf-8")
    parent = tmp_path / "parent.py"
    parent.write_text(
        "import subprocess, sys\n"
        "subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2]],\n"
        "                 close_fds=True)\n", encoding="utf-8")

    subprocess.run([sys.executable, str(parent), str(script), str(marker)],
                   check=True, timeout=30)
    deadline = time.time() + 10
    while time.time() < deadline and not marker.is_file():
        time.sleep(0.05)
    assert marker.is_file(), "the child died with its parent"
    assert marker.read_text() == "alive"

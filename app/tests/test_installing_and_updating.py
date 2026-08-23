"""Installing the app, and updating it, without losing anything of his.

One action does both. Mark unzips a package, double-clicks
`Install or update Roy R. Fisher.bat`, and afterwards one Desktop icon starts
the newest version. Doing it again with a newer package repoints the icon and
leaves the version he had in place.

The promise these tests exist to hold is that an update cannot cost him
anything. His key, the folder his jobs live in, his settings, his usage
history, his classifications and every document he has built all live outside
any version folder, so the installer copies into a version folder and can
reach none of them. That is asserted here by putting real files in all of
those places, updating, and reading them back.

Real folders on this Mac throughout, with `RRF_INSTALL_HOME` and `RRF_DESKTOP`
pointed into a temporary directory. What cannot be tested here is Windows
itself: a real `.lnk`, `%LOCALAPPDATA%`, and Explorer's unzip. Those are named
in the handoff as the acceptance test, not asserted here.
"""
import json
import os
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))
sys.path.insert(0, str(APP))

import install_windows as installer  # noqa: E402
import packaging  # noqa: E402
import startup  # noqa: E402


def make_package(where: Path, version: str) -> Path:
    """A folder shaped like a built package: a VERSION, a launcher, an app,
    a practice job, and a MANIFEST covering all of it."""
    where.mkdir(parents=True)
    (where / "VERSION").write_text(version + "\n", encoding="utf-8")
    (where / installer.LAUNCHER_NAME).write_text("@echo off\r\n", encoding="utf-8")
    (where / "Install or update Roy R. Fisher.bat").write_text("@echo off\r\n",
                                                               encoding="utf-8")
    (where / "README FIRST.txt").write_text("Roy R. Fisher\n", encoding="utf-8")
    (where / "app").mkdir()
    (where / "app" / "run_app.py").write_text("# %s\n" % version, encoding="utf-8")
    (where / "app" / "install_windows.py").write_text("# installer\n", encoding="utf-8")
    (where / "python").mkdir()
    (where / "python" / "python.exe").write_bytes(b"not really an interpreter")
    demo = where / packaging.DEMO_DIR / "ANYTOWN_100 Example Avenue - 2026" / "Photos"
    demo.mkdir(parents=True)
    (demo / "photo-01.jpg").write_bytes(b"a photo")
    (where / packaging.MANIFEST_NAME).write_text(packaging.build_manifest(where),
                                                 encoding="utf-8")
    return where


@pytest.fixture
def place(tmp_path, monkeypatch):
    """An install home and a Desktop, both temporary, and no PowerShell."""
    home = tmp_path / "LocalAppData" / "Roy R. Fisher"
    desktop = tmp_path / "Desktop"
    desktop.mkdir(parents=True)
    monkeypatch.setenv("RRF_INSTALL_HOME", str(home))
    monkeypatch.setenv("RRF_DESKTOP", str(desktop))
    # No Windows here, so the .lnk branch cannot succeed. Forcing the fallback
    # keeps the test about installing rather than about PowerShell.
    monkeypatch.setattr(installer.subprocess, "run",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("no powershell")))
    return tmp_path, home, desktop


# --- the first install ----------------------------------------------------
def test_it_installs_into_its_own_version_folder(place, tmp_path):
    _, home, _ = place
    done = installer.install(make_package(tmp_path / "unzipped", "0.3.0"))
    assert done["version"] == "0.3.0"
    assert Path(done["installed_to"]) == home / "0.3.0"
    assert (home / "0.3.0" / installer.LAUNCHER_NAME).is_file()
    assert (home / "0.3.0" / "app" / "run_app.py").read_text() == "# 0.3.0\n"


def test_it_puts_one_thing_on_the_desktop_that_starts_it(place, tmp_path):
    _, home, desktop = place
    done = installer.install(make_package(tmp_path / "unzipped", "0.3.0"))
    icon = Path(done["icon"])
    assert icon.parent == desktop
    assert icon.is_file()
    assert str(home / "0.3.0") in icon.read_text()
    assert installer.LAUNCHER_NAME in icon.read_text()


def test_the_first_install_does_not_talk_about_going_back(place, tmp_path):
    _, _, _ = place
    done = installer.install(make_package(tmp_path / "unzipped", "0.3.0"))
    assert done["updated"] is False
    assert done["previous"] == []


def test_the_unzipped_folder_is_not_needed_afterwards(place, tmp_path):
    import shutil
    _, home, _ = place
    source = make_package(tmp_path / "unzipped", "0.3.0")
    installer.install(source)
    shutil.rmtree(source)
    assert (home / "0.3.0" / "app" / "run_app.py").is_file()


def test_the_installed_copy_verifies_against_its_own_manifest(place, tmp_path):
    _, home, _ = place
    installer.install(make_package(tmp_path / "unzipped", "0.3.0"))
    packaging.verify(home / "0.3.0")          # raises if anything is wrong


def test_a_runtime_file_is_never_carried_across(place, tmp_path):
    """It describes a running app on the machine that built it."""
    _, home, _ = place
    source = make_package(tmp_path / "unzipped", "0.3.0")
    startup.write_runtime(source, 51234, "0.3.0")
    installer.install(source)
    assert not (home / "0.3.0" / startup.RUNTIME_NAME).exists()


# --- updating -------------------------------------------------------------
def test_the_same_action_updates(place, tmp_path):
    _, home, desktop = place
    installer.install(make_package(tmp_path / "v3", "0.3.0"))
    done = installer.install(make_package(tmp_path / "v4", "0.4.0"))

    assert done["updated"] is True
    assert done["version"] == "0.4.0"
    assert (home / "0.4.0" / "app" / "run_app.py").read_text() == "# 0.4.0\n"
    icon = Path(done["icon"])
    assert str(home / "0.4.0") in icon.read_text(), "the icon starts the new one"


def test_the_version_he_had_is_still_there(place, tmp_path):
    _, home, _ = place
    installer.install(make_package(tmp_path / "v3", "0.3.0"))
    done = installer.install(make_package(tmp_path / "v4", "0.4.0"))
    assert (home / "0.3.0" / installer.LAUNCHER_NAME).is_file()
    assert done["previous"] == ["0.3.0"]


def test_one_click_goes_back_to_the_previous_version(place, tmp_path):
    _, home, _ = place
    installer.install(make_package(tmp_path / "v3", "0.3.0"))
    installer.install(make_package(tmp_path / "v4", "0.4.0"))
    rollback = home / installer.ROLLBACK_NAME
    assert rollback.is_file()
    text = rollback.read_text()
    assert installer.LAUNCHER_NAME in text
    assert "0.3.0" in text, "the version to go back to is named, not worked out"
    assert "0.4.0" not in text, "it must not start the version that just failed"


def test_the_version_to_go_back_to_is_chosen_by_number(place, tmp_path):
    """`dir /o-n` would sort text and put 0.9.0 above 0.10.0."""
    _, home, _ = place
    installer.install(make_package(tmp_path / "a", "0.9.0"))
    installer.install(make_package(tmp_path / "b", "0.10.0"))
    installer.install(make_package(tmp_path / "c", "0.11.0"))
    assert "0.10.0" in (home / installer.ROLLBACK_NAME).read_text()


def test_with_only_one_version_it_says_there_is_nowhere_to_go(place, tmp_path):
    _, home, _ = place
    installer.install(make_package(tmp_path / "a", "0.3.0"))
    text = (home / installer.ROLLBACK_NAME).read_text()
    assert "nothing to go back to" in text
    assert installer.LAUNCHER_NAME not in text


def test_installing_the_same_version_twice_is_not_a_failure(place, tmp_path):
    _, home, _ = place
    installer.install(make_package(tmp_path / "a", "0.3.0"))
    again = make_package(tmp_path / "b", "0.3.0")
    (again / "app" / "run_app.py").write_text("# rebuilt\n", encoding="utf-8")
    (again / packaging.MANIFEST_NAME).write_text(packaging.build_manifest(again),
                                                 encoding="utf-8")
    installer.install(again)
    assert (home / "0.3.0" / "app" / "run_app.py").read_text() == "# rebuilt\n"


def test_only_a_bounded_number_of_versions_is_kept(place, tmp_path):
    _, home, _ = place
    for n, v in enumerate(["0.1.0", "0.2.0", "0.3.0", "0.4.0", "0.5.0"]):
        installer.install(make_package(tmp_path / ("p%d" % n), v))
    kept = sorted(p.name for p in home.iterdir() if p.is_dir())
    assert kept == ["0.3.0", "0.4.0", "0.5.0"]


def test_versions_are_ordered_by_number_not_by_name(place, tmp_path):
    _, home, _ = place
    for n, v in enumerate(["0.9.0", "0.10.0"]):
        installer.install(make_package(tmp_path / ("p%d" % n), v))
    assert [p.name for p in installer.version_folders(home)] == ["0.10.0", "0.9.0"]


# --- what an update must never cost him -----------------------------------
def test_an_update_leaves_every_file_of_his_alone(place, tmp_path, monkeypatch):
    """The whole promise, asserted against real files in all six places."""
    _, home, _ = place
    his = tmp_path / "his home"
    his.mkdir()
    jobs = tmp_path / "RRF Jobs" / "DAVENPORT_1 Main Street - 2026" / "Photos"
    jobs.mkdir(parents=True)

    owned = {
        "key": (his / ".rrf-app.env", "ANTHROPIC_API_KEY=sk-ant-his-own-key\n"),
        "settings": (his / ".rrf-app.json",
                     json.dumps({"jobs_folder": str(jobs.parents[1]),
                                 "workspaces": {str(jobs.parents[1]): {"active": ["DAVENPORT_1 Main Street - 2026"]}}})),
        "usage": (his / ".rrf-ai-usage.json", json.dumps({"runs": [{"cost": 1.23}]})),
        "classifications": (his / ".rrf-classifications.json",
                            json.dumps({"a job": {"brief.pdf": "Engagement letter"}})),
        "job facts": (his / ".rrf-job-facts.json", json.dumps({"a job": {"city": "Davenport"}})),
        "document": (jobs / "Davenport_1 Main Street Photos (Complete).docx",
                     "a built document"),
    }
    for _, (path, body) in owned.items():
        path.write_text(body, encoding="utf-8")

    installer.install(make_package(tmp_path / "v3", "0.3.0"))
    installer.install(make_package(tmp_path / "v4", "0.4.0"))

    for what, (path, body) in owned.items():
        assert path.is_file(), "%s was removed by the update" % what
        assert path.read_text(encoding="utf-8") == body, "%s was changed" % what


def test_nothing_is_written_outside_the_install_home_and_the_desktop(place, tmp_path):
    _, home, desktop = place
    source = make_package(tmp_path / "unzipped", "0.3.0")
    before = {p for p in tmp_path.rglob("*")}
    installer.install(source)
    fresh = {p for p in tmp_path.rglob("*")} - before
    stray = [str(p) for p in fresh
             if home not in p.parents and p != home
             and desktop not in p.parents
             and home.parent not in (p,)]
    assert stray == []


# --- refusing rather than half-finishing ----------------------------------
def test_a_damaged_package_is_refused_before_anything_is_copied(place, tmp_path):
    _, home, _ = place
    source = make_package(tmp_path / "unzipped", "0.3.0")
    (source / "app" / "run_app.py").write_text("# tampered with\n", encoding="utf-8")
    with pytest.raises(installer.InstallRefused) as refused:
        installer.install(source)
    assert "MANIFEST" in refused.value.message or "unzip" in refused.value.message.lower()
    assert not home.exists()


def test_a_package_with_no_version_is_refused(place, tmp_path):
    _, home, _ = place
    source = make_package(tmp_path / "unzipped", "0.3.0")
    (source / "VERSION").write_text("\n", encoding="utf-8")
    (source / packaging.MANIFEST_NAME).write_text(packaging.build_manifest(source),
                                                  encoding="utf-8")
    with pytest.raises(installer.InstallRefused):
        installer.install(source)


def test_it_refuses_while_a_version_is_running(place, tmp_path, monkeypatch):
    _, home, _ = place
    installer.install(make_package(tmp_path / "v3", "0.3.0"))
    startup.write_runtime(home / "0.3.0", 51234, "0.3.0")
    monkeypatch.setattr(installer.startup, "ask_version", lambda *a, **k: "0.3.0")

    with pytest.raises(installer.InstallRefused) as refused:
        installer.install(make_package(tmp_path / "v4", "0.4.0"))
    assert "running" in refused.value.message.lower()
    assert not (home / "0.4.0").exists(), "nothing was copied"


def test_a_stale_runtime_file_does_not_block_an_update(place, tmp_path, monkeypatch):
    """A version that was closed leaves one behind. That is not a reason."""
    _, home, _ = place
    installer.install(make_package(tmp_path / "v3", "0.3.0"))
    startup.write_runtime(home / "0.3.0", 51234, "0.3.0")
    monkeypatch.setattr(installer.startup, "ask_version", lambda *a, **k: "")
    installer.install(make_package(tmp_path / "v4", "0.4.0"))
    assert (home / "0.4.0").is_dir()


# --- where it decides to put things ---------------------------------------
def test_it_installs_under_local_app_data_on_windows(monkeypatch, tmp_path):
    monkeypatch.delenv("RRF_INSTALL_HOME", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))
    assert installer.install_home() == tmp_path / "AppData" / "Local" / "Roy R. Fisher"


def test_a_redirected_onedrive_desktop_is_preferred(monkeypatch, tmp_path):
    """Backup moves the Desktop, and the old path still exists but is not the
    one he looks at."""
    monkeypatch.delenv("RRF_DESKTOP", raising=False)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    (tmp_path / "Desktop").mkdir()
    (tmp_path / "OneDrive" / "Desktop").mkdir(parents=True)
    assert installer.desktop_folder() == tmp_path / "OneDrive" / "Desktop"


def test_the_ordinary_desktop_is_used_when_there_is_no_onedrive(monkeypatch, tmp_path):
    monkeypatch.delenv("RRF_DESKTOP", raising=False)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    (tmp_path / "Desktop").mkdir()
    assert installer.desktop_folder() == tmp_path / "Desktop"


# --- the shim, and what ships ---------------------------------------------
def test_the_batch_file_only_calls_python():
    shim = (APP.parent / "Install or update Roy R. Fisher.bat").read_text()
    assert "python\\python.exe app\\install_windows.py" in shim
    assert "pause" in shim, "the window has to stay open long enough to read"


def test_the_installer_travels_with_the_package_it_installs():
    packager = (APP.parent / "tools" / "package_windows.py").read_text()
    assert 'shutil.copy2(REPO / "app" / "install_windows.py"' in packager
    assert '"Install or update Roy R. Fisher.bat"' in packager

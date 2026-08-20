"""What the package contains, and how a damaged copy is caught.

These run against a tree the committed packaging script actually produced, not
a hand-assembled imitation. That distinction is the point: the previous plan
proposed asserting "against a built package tree" with nothing in the
repository building one, and a test that checks an artifact no script produces
is a test that gets run once.

The script is run with --offline here, so the layout, the exclusions and the
manifest are all real while the 12 MB interpreter and the wheels are not
downloaded on every test run. Whether those import on Windows is a Gate A
question and no test on a Mac can answer it.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import packaging  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tools" / "package_windows.py"

# The build needs the web interface. On a clone that has never run npm it is
# absent, and this skips the way the corpus tests do rather than failing.
DIST = REPO / "app" / "web" / "dist" / "index.html"
needs_dist = pytest.mark.skipif(
    not DIST.is_file(),
    reason="app/web/dist is not built; run: cd app/web && npm ci && npm run build")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """One real package, built once by the committed script."""
    if not DIST.is_file():
        pytest.skip("app/web/dist is not built")
    out = tmp_path_factory.mktemp("package") / "Roy R. Fisher v0.1.0"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out),
         "--work", str(out.parent / "cache"), "--offline"],
        capture_output=True, text=True, cwd=str(REPO))
    if result.returncode != 0:
        # A stale dist is an ordinary state mid-edit, not a broken test. The
        # script refuses to package one, correctly, and forty-five errors is
        # the wrong way to say "rebuild the interface".
        if "older than" in (result.stdout + result.stderr):
            pytest.skip("app/web/dist is stale; run: cd app/web && npm run build")
        raise AssertionError(result.stdout + result.stderr)
    return out


@pytest.fixture
def copy(built, tmp_path):
    """A throwaway copy, so a test may damage it."""
    place = tmp_path / built.name
    shutil.copytree(built, place)
    return place


# --- what is in it ----------------------------------------------------------

@needs_dist
def test_the_script_produces_a_package_that_verifies(built):
    packaging.verify(built)


@needs_dist
@pytest.mark.parametrize("required", [
    "VERSION", "MANIFEST", "Start Roy R. Fisher.bat", "README FIRST.txt",
    "app/run_app.py", "app/server/main.py", "app/server/packaging.py",
    "app/server/startup.py", "app/engine/photo_pages.py",
    "app/templates/Photo.docx", "app/data/engagement-matrix.md",
    "app/web/dist/index.html",
])
def test_every_required_path_is_present(built, required):
    assert (built / required).exists(), required


@needs_dist
@pytest.mark.parametrize("excluded", [
    "app/tests", "app/web/src", "app/web/node_modules", "app/web/package.json",
    "app/web/package-lock.json", "app/server/demo.py", "brand", "docs",
    ".git", "RRF Demo Jobs", "Report Examples", "locker", "tools",
    "Start Roy R. Fisher.command", "runtime.json",
])
def test_every_excluded_path_is_absent(built, excluded):
    assert not (built / excluded).exists(), excluded


@needs_dist
def test_no_key_env_cache_or_noise_travelled(built):
    for pattern in ("*.env", "**/__pycache__", "**/.DS_Store", "**/*.pyc",
                    "**/.pytest_cache", "**/.rrf-thumbs"):
        assert not list(built.glob(pattern)), pattern


@needs_dist
def test_the_demo_route_source_is_not_in_the_package(built):
    """demo.py is excluded, and main.py must not be the only thing standing
    between Mark and the reset button."""
    assert not (built / "app" / "server" / "demo.py").exists()


# --- the manifest itself ----------------------------------------------------

@needs_dist
def test_the_manifest_does_not_list_itself_or_runtime_json(built):
    listed = packaging.read_manifest(built)
    assert "MANIFEST" not in listed["files"]
    assert "runtime.json" not in listed["files"]


@needs_dist
def test_the_manifest_records_the_version_and_an_aggregate(built):
    listed = packaging.read_manifest(built)
    assert listed["version"] == packaging.version_of(built)
    assert listed["aggregate"].startswith("sha256:")
    assert len(listed["aggregate"].split(":")[1]) == 64
    assert len(listed["files"]) > 10


@needs_dist
def test_building_twice_from_the_same_inputs_gives_the_same_manifest(built, tmp_path):
    again = tmp_path / built.name
    subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(again),
         "--work", str(tmp_path / "cache"), "--offline"],
        check=True, capture_output=True, text=True, cwd=str(REPO))
    first = packaging.read_manifest(built)
    second = packaging.read_manifest(again)
    assert first["aggregate"] == second["aggregate"]
    assert first["files"] == second["files"]


# --- catching a damaged copy ------------------------------------------------

@needs_dist
def test_a_missing_file_is_caught_and_named(copy):
    (copy / "app" / "server" / "main.py").unlink()
    with pytest.raises(packaging.PackageDamaged) as raised:
        packaging.verify(copy)
    assert "app/server/main.py" in raised.value.message
    assert "unzip" in raised.value.message.lower()
    assert "Traceback" not in raised.value.message


@needs_dist
def test_a_truncated_file_is_caught_and_named(copy):
    target = copy / "app" / "server" / "main.py"
    target.write_bytes(target.read_bytes()[:20])
    with pytest.raises(packaging.PackageDamaged) as raised:
        packaging.verify(copy)
    assert "wrong size" in raised.value.message
    assert "app/server/main.py" in raised.value.message


@needs_dist
def test_corruption_that_keeps_the_size_is_still_caught(copy):
    """Size alone would miss this. The aggregate is what catches it."""
    target = copy / "app" / "server" / "main.py"
    body = bytearray(target.read_bytes())
    body[10] = body[10] ^ 0xFF
    target.write_bytes(bytes(body))
    with pytest.raises(packaging.PackageDamaged) as raised:
        packaging.verify(copy)
    assert "do not match" in raised.value.message


@needs_dist
def test_a_file_moved_within_the_package_is_caught(copy):
    shutil.move(str(copy / "app" / "server" / "startup.py"),
                str(copy / "app" / "startup.py"))
    with pytest.raises(packaging.PackageDamaged):
        packaging.verify(copy)


@needs_dist
def test_a_missing_manifest_is_caught(copy):
    (copy / "MANIFEST").unlink()
    with pytest.raises(packaging.PackageDamaged) as raised:
        packaging.verify(copy)
    assert "MANIFEST" in raised.value.message


# --- runtime.json cannot invalidate the package -----------------------------

@needs_dist
def test_the_package_still_verifies_after_a_normal_start(copy):
    """The contradiction this design had to fix: runtime.json used to be
    inside the package, so the app invalidated its own copy the first time it
    ran."""
    sys.path.insert(0, str(REPO / "app" / "server"))
    import startup

    packaging.verify(copy)
    startup.write_runtime(copy, 51234, "0.1.0")
    packaging.verify(copy)                       # after the first start
    startup.write_runtime(copy, 51999, "0.1.0")
    packaging.verify(copy)                       # and after the second


# --- the practice job ------------------------------------------------------

@needs_dist
def test_the_practice_job_ships_beside_the_launcher(built):
    demo = built / "Demo Jobs"
    assert demo.is_dir()
    jobs = [p for p in demo.iterdir() if p.is_dir()]
    assert len(jobs) == 1
    assert (jobs[0] / "job-brief.md").is_file()
    assert len(list((jobs[0] / "Photos").iterdir())) == 12


@needs_dist
def test_the_practice_job_is_not_in_the_immutable_manifest(built):
    """Shipped content, but Mark's to work in. Opening it writes a photo
    manifest and building writes a document, and a listed folder would mean
    the app refused to start the moment he used the demo it came with."""
    listed = packaging.read_manifest(built)
    assert not [p for p in listed["files"] if p.startswith("Demo Jobs/")]


@needs_dist
def test_the_package_still_verifies_after_the_demo_is_used(copy):
    """The defect this closes was found by shipping the folder and then
    using it: a photo manifest and a built document appear inside Demo Jobs,
    and verify() counts anything unlisted as a damaged package."""
    packaging.verify(copy)

    job = next(p for p in (copy / "Demo Jobs").iterdir() if p.is_dir())
    (job / "Photos" / "photo-manifest.json").write_text("{}", encoding="utf-8")
    (job / "Photos" / "Photo (RRF App).docx").write_bytes(b"a built document")
    (job / "Photos" / ".rrf-thumbs").mkdir()
    (job / "Photos" / ".rrf-thumbs" / "01.jpg").write_bytes(b"a thumbnail")

    packaging.verify(copy)


@needs_dist
def test_the_development_demo_system_did_not_come_back(built):
    """A practice dataset is not Reset Demo. demo.py, the routes and the
    baseline all stay out."""
    assert not (built / "app" / "server" / "demo.py").exists()
    assert not (built / ".rrf-demo.json").exists()
    assert not (built / ".rrf-demo-baseline").exists()
    assert not (built / "RRF Demo Jobs").exists()


# --- the package actually runs ----------------------------------------------

@needs_dist
def test_the_packaged_app_imports_without_demo_py(built):
    """The defect this catches was real and only a real package showed it.

    `main.py` imported `demo` at module scope and referenced `demo.DemoError`
    in a decorator. Excluding demo.py from the package therefore stopped the
    whole server importing, so the app did not start at all on Mark's machine
    while every test on the Mac stayed green. Section 10a predicted it in
    words; nothing proved it until a package was built and run.
    """
    result = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, %r); import main; "
         "app = main.create_app(); "
         "print(sorted(r.path for r in app.routes if 'demo' in r.path))"
         % str(built / "app" / "server")],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]"          # neither demo route exists


@needs_dist
def test_the_packaged_app_serves_its_own_version(built):
    """/api/version has to answer inside the package, because it is what the
    launcher probes to decide whether the thing on a port is us."""
    result = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, %r); "
         "from fastapi.testclient import TestClient; import main; "
         "print(TestClient(main.create_app()).get('/api/version').json()['version'])"
         % str(built / "app" / "server")],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == packaging.version_of(built)


# --- the script is the only builder -----------------------------------------

def test_the_packaging_script_is_committed():
    assert SCRIPT.is_file()
    text = SCRIPT.read_text(encoding="utf-8")
    # It resolves the closure rather than carrying a written list of packages.
    assert "pip" in text and "download" in text
    for hand_written in ("fastapi==", "pillow==", "anthropic=="):
        assert hand_written not in text, hand_written


def test_the_script_knows_httpx_is_not_test_only():
    """The Task 1 correction. anthropic requires httpx at runtime, so a
    package without it fails on Mark's machine and nowhere else."""
    text = SCRIPT.read_text(encoding="utf-8")
    assert '"pytest"' in text
    assert '"httpx"' not in text.split("TEST_ONLY")[1].split(")")[0]

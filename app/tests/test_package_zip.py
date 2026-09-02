"""The archive Mark downloads, and the hash that names the exact one.

Task 3 produced a folder. The approved delivery path is a private download
link, and you cannot link to a folder, so this covers the archive itself: one
top-level folder, nothing unsafe in it, the same bytes every build, and a
sidecar hash that identifies the build Spenser approved.

Most tests here run against a small synthetic package so determinism can be
proved in a second rather than in three minutes. Two run against the real
archive when it has been built, and skip when it has not.

None of this is the Gate A test. Extracting a ZIP with Python on a Mac says
nothing about Windows Explorer, SmartScreen, or whether the embedded
interpreter starts.
"""
import hashlib
import io
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import packaging  # noqa: E402
import package_windows as pw  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
REAL = REPO / "build" / "packages"
# Read from VERSION rather than written here, so a version bump does not
# silently turn every real-archive test into a skip. It did once.
REAL_VERSION = packaging.version_of(REPO) or "0.0.0"
REAL_NAME = "Roy R. Fisher v%s" % REAL_VERSION
REAL_ZIP = REAL / ("%s.zip" % REAL_NAME)

needs_real = pytest.mark.skipif(
    not REAL_ZIP.is_file(),
    reason="the real archive is not built; run: python3 tools/package_windows.py")


@pytest.fixture
def fake(tmp_path):
    """A small package with the shape of the real one, built by hand.

    Small on purpose. Determinism and path safety are properties of the
    archiver, and proving them on four files is the same proof as on 2,472,
    and finishes fast enough that the tests get run.
    """
    folder = tmp_path / "Roy R. Fisher v0.1.0"
    (folder / "app" / "server").mkdir(parents=True)
    (folder / "python" / "site-packages").mkdir(parents=True)
    (folder / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (folder / "Start Roy R. Fisher.bat").write_text("@echo off\n", encoding="utf-8")
    (folder / "README FIRST.txt").write_text("Unzip me.\n", encoding="utf-8")
    (folder / "app" / "run_app.py").write_text("# launcher\n", encoding="utf-8")
    (folder / "app" / "server" / "main.py").write_text("# server\n", encoding="utf-8")
    (folder / "python" / "python.exe").write_bytes(b"MZ not really\n")
    (folder / packaging.MANIFEST_NAME).write_text(
        packaging.build_manifest(folder), encoding="utf-8")
    return folder


def build_zip(folder: Path):
    zip_path = folder.with_name(folder.name + ".zip")
    pw.make_zip(folder, zip_path)
    sidecar = pw.write_sidecar(zip_path)
    return zip_path, sidecar


# --- shape ------------------------------------------------------------------

def test_it_makes_the_zip_and_the_sidecar(fake):
    zip_path, sidecar = build_zip(fake)
    assert zip_path.is_file()
    assert sidecar.is_file()
    assert sidecar.name == "Roy R. Fisher v0.1.0.zip.sha256"


def test_there_is_exactly_one_top_level_folder(fake):
    zip_path, _ = build_zip(fake)
    with zipfile.ZipFile(zip_path) as archive:
        tops = {n.split("/")[0] for n in archive.namelist()}
    assert tops == {"Roy R. Fisher v0.1.0"}


def test_every_required_file_is_inside(fake):
    zip_path, _ = build_zip(fake)
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
    for required in ("VERSION", "MANIFEST", "Start Roy R. Fisher.bat",
                     "README FIRST.txt", "app/run_app.py",
                     "app/server/main.py", "python/python.exe"):
        assert "Roy R. Fisher v0.1.0/%s" % required in names, required


def test_runtime_json_is_never_archived(fake):
    """It is written at startup, after the package check has passed. An
    archived one would be a port from another machine."""
    sys.path.insert(0, str(REPO / "app" / "server"))
    import startup

    startup.write_runtime(fake, 51234, "0.1.0")
    (fake / packaging.MANIFEST_NAME).write_text(
        packaging.build_manifest(fake), encoding="utf-8")
    zip_path, _ = build_zip(fake)
    with zipfile.ZipFile(zip_path) as archive:
        assert not [n for n in archive.namelist() if n.endswith("runtime.json")]


def test_the_zip_does_not_contain_itself_or_its_sidecar(fake):
    build_zip(fake)
    zip_path, _ = build_zip(fake)              # second pass, both now exist
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
    assert not [n for n in names if n.endswith(".zip")]
    assert not [n for n in names if n.endswith(".sha256")]


# --- safety -----------------------------------------------------------------

def test_no_entry_escapes_the_top_folder(fake):
    zip_path, _ = build_zip(fake)
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            assert not name.startswith("/")
            assert ".." not in name.split("/")
            assert ":" not in name
            assert "\\" not in name
            assert name.startswith("Roy R. Fisher v0.1.0/")


def test_a_link_in_the_package_is_refused_rather_than_archived(fake):
    (fake / "app" / "elsewhere.py").symlink_to(fake / "app" / "run_app.py")
    with pytest.raises(pw.UnsafeArchivePath):
        pw.make_zip(fake, fake.with_name(fake.name + ".zip"))


def test_no_symlink_entries_are_written(fake):
    zip_path, _ = build_zip(fake)
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            mode = info.external_attr >> 16
            assert not (mode & 0o170000) == 0o120000, info.filename


# --- the sidecar ------------------------------------------------------------

def test_the_sidecar_matches_the_zip(fake):
    zip_path, sidecar = build_zip(fake)
    digest, name = sidecar.read_text(encoding="utf-8").strip().split("  ")
    assert name == zip_path.name
    assert digest == hashlib.sha256(zip_path.read_bytes()).hexdigest()
    assert len(digest) == 64


def test_a_changed_zip_no_longer_matches_its_sidecar(fake):
    zip_path, sidecar = build_zip(fake)
    recorded = sidecar.read_text(encoding="utf-8").split("  ")[0]
    body = bytearray(zip_path.read_bytes())
    body[-1] = body[-1] ^ 0xFF
    zip_path.write_bytes(bytes(body))
    assert hashlib.sha256(zip_path.read_bytes()).hexdigest() != recorded


# --- determinism ------------------------------------------------------------

def test_two_builds_give_byte_identical_archives(fake, tmp_path):
    first = tmp_path / "one.zip"
    second = tmp_path / "two.zip"
    pw.make_zip(fake, first)
    pw.make_zip(fake, second)
    assert first.read_bytes() == second.read_bytes()
    assert pw.sha256_of(first) == pw.sha256_of(second)


def test_timestamps_and_permissions_are_normalised(fake):
    """Real mtimes and real modes would change the bytes between builds, and
    the hash has to name one artifact rather than one moment."""
    zip_path, _ = build_zip(fake)
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            assert info.date_time == pw.ZIP_EPOCH
            assert info.create_system == 3
            mode = info.external_attr >> 16
            assert mode in (pw.FILE_MODE, pw.DIR_MODE), oct(mode)


def test_the_entry_order_is_deterministic(fake, tmp_path):
    first = tmp_path / "one.zip"
    pw.make_zip(fake, first)
    with zipfile.ZipFile(first) as archive:
        names = archive.namelist()
    assert names == sorted(names)


# --- extraction -------------------------------------------------------------

def test_extraction_passes_the_internal_manifest(fake, tmp_path):
    zip_path, _ = build_zip(fake)
    holder = tmp_path / "fresh"
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(holder)
    packaging.verify(holder / fake.name)


def test_the_verifier_accepts_a_good_archive(fake):
    zip_path, _ = build_zip(fake)
    facts = pw.verify_zip(fake, zip_path)
    assert facts["matches_folder"] is True
    assert facts["entries"] >= 7


@pytest.mark.parametrize("damage", ["missing", "truncated", "same_size"])
def test_a_damaged_file_fails_the_manifest_after_extraction(fake, tmp_path, damage):
    zip_path, _ = build_zip(fake)
    holder = tmp_path / "fresh"
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(holder)
    target = holder / fake.name / "app" / "server" / "main.py"

    if damage == "missing":
        target.unlink()
    elif damage == "truncated":
        target.write_bytes(target.read_bytes()[:2])
    else:
        body = bytearray(target.read_bytes())
        body[0] = body[0] ^ 0xFF
        target.write_bytes(bytes(body))

    with pytest.raises(packaging.PackageDamaged):
        packaging.verify(holder / fake.name)


def test_the_verifier_removes_only_its_own_temporary_directory(fake, tmp_path):
    import tempfile

    before = set(Path(tempfile.gettempdir()).glob("rrf-zip-check-*"))
    zip_path, _ = build_zip(fake)
    pw.verify_zip(fake, zip_path)
    after = set(Path(tempfile.gettempdir()).glob("rrf-zip-check-*"))
    assert after == before
    assert fake.is_dir() and zip_path.is_file()


# --- nothing private travels ------------------------------------------------

def test_no_source_demo_evidence_key_or_home_state_is_archived(fake):
    zip_path, _ = build_zip(fake)
    with zipfile.ZipFile(zip_path) as archive:
        names = " ".join(archive.namelist())
        blob = b" ".join(archive.read(n) for n in archive.namelist())

    for forbidden in ("app/tests", "app/web/src", "node_modules", "package.json",
                      "demo.py", "TEST JOBS", "Report Examples", "locker",
                      "brand/", "docs/", ".git/", ".rrf-app.json",
                      ".rrf-app.env", ".rrf-classifications.json", ".env"):
        assert forbidden not in names, forbidden
    for secret in (b"sk-ant", b"ANTHROPIC_API_KEY"):
        assert secret not in blob, secret


# --- the real archive -------------------------------------------------------

@needs_real
def test_the_real_archive_has_one_folder_and_no_unsafe_paths():
    with zipfile.ZipFile(REAL_ZIP) as archive:
        names = archive.namelist()
    assert {n.split("/")[0] for n in names} == {REAL_NAME}
    for name in names:
        assert not name.startswith("/") and ".." not in name.split("/")


@needs_real
@pytest.mark.parametrize("excluded", [
    "app/tests", "app/web/src", "app/web/node_modules", "app/server/demo.py",
    "tools", "brand", "docs", "TEST JOBS", "Report Examples", "locker",
    "Start Roy R. Fisher.command", "runtime.json",
])
def test_the_real_archive_excludes_everything_it_must(excluded):
    """Anchored at the top of the package, which is what these paths mean.

    Two looser forms were wrong before this one. A substring test called the
    package broken because "tools" is inside "httptools". Matching a component
    anywhere was wrong too: the anthropic SDK ships its own
    `anthropic/lib/tools/`, which is nothing to do with this repository's
    `tools/` directory. What is excluded is the path at the package root.
    """
    wanted = excluded.split("/")
    with zipfile.ZipFile(REAL_ZIP) as archive:
        for name in archive.namelist():
            parts = name.split("/")[1:]          # drop the top folder
            assert parts[:len(wanted)] != wanted, name


@needs_real
def test_the_real_archive_carries_the_windows_runtime_and_closure():
    with zipfile.ZipFile(REAL_ZIP) as archive:
        names = " ".join(archive.namelist())
    assert "python/python314.zip" in names or "python/python.exe" in names
    for present in ("httpx/", "pillow_heif/", "PIL/", "pydantic_core/",
                    "lxml/", "jiter/", "httptools/", "watchfiles/",
                    "websockets/", "yaml/", "colorama/"):
        assert present in names, present

    # The uvloop distribution must be absent: it is POSIX-only and has no
    # Windows wheel at all. uvicorn's own `loops/uvloop.py` is a different
    # thing, an adapter that imports uvloop when it happens to be installed,
    # and it ships with uvicorn on every platform. An earlier version of this
    # test confused the two and called a correct package broken.
    with zipfile.ZipFile(REAL_ZIP) as archive:
        entries = archive.namelist()
    assert not [n for n in entries if "/site-packages/uvloop/" in n]
    assert not [n for n in entries if "/uvloop-" in n and ".dist-info" in n]


@needs_real
def test_the_real_sidecar_matches_the_real_archive():
    sidecar = REAL_ZIP.with_name(REAL_ZIP.name + ".sha256")
    digest, name = sidecar.read_text(encoding="utf-8").strip().split("  ")
    assert name == REAL_ZIP.name
    assert digest == pw.sha256_of(REAL_ZIP)


@needs_real
def test_the_real_archive_carries_the_practice_job():
    with zipfile.ZipFile(REAL_ZIP) as archive:
        names = archive.namelist()
    photos = [n for n in names
              if "/Demo Jobs/" in n and "/Photos/" in n and not n.endswith("/")]
    assert len(photos) == 73, "twelve for the ordinary run and sixty-one for the tranching"

    by_job = {}
    for n in photos:
        by_job.setdefault(n.split("/Demo Jobs/")[1].split("/")[0], []).append(n)
    assert sorted(len(v) for v in by_job.values()) == [12, 61], by_job.keys()
    assert any("61 Photo Test" in name for name in by_job)
    assert [n for n in names if n.endswith("/Demo Jobs/READ ME.txt")]
    assert [n for n in names if "/Demo Jobs/" in n and n.endswith("job-brief.md")]


@needs_real
def test_the_practice_job_photos_carry_no_metadata():
    """Checked in the archive itself, not in the folder it was built from."""
    from PIL import Image

    with zipfile.ZipFile(REAL_ZIP) as archive:
        for name in archive.namelist():
            if "/Demo Jobs/" not in name or not name.lower().endswith((".jpg", ".png")):
                continue
            with Image.open(io.BytesIO(archive.read(name))) as image:
                exif = image.getexif()
            assert not exif, name
            assert 0x8825 not in exif, name


@needs_real
def test_the_archive_carries_no_client_material_from_the_corpus():
    """Names of real jobs, addresses and clients, checked as bytes across
    every file in the archive."""
    with zipfile.ZipFile(REAL_ZIP) as archive:
        for name in archive.namelist():
            if name.endswith("/") or "/Demo Jobs/" not in name:
                continue
            blob = archive.read(name)
            for forbidden in (b"Bettendorf", b"Davenport", b"Mason City",
                              b"Walmart", b"Brady Street", b"sk-ant"):
                assert forbidden not in blob, "%s in %s" % (forbidden, name)


@needs_real
def test_the_real_archive_carries_no_build_machine_paths():
    """direct_url.json used to record file:///Users/<name>/... for every
    distribution, so the build machine's username shipped to Mark."""
    with zipfile.ZipFile(REAL_ZIP) as archive:
        assert not [n for n in archive.namelist() if n.endswith("direct_url.json")]


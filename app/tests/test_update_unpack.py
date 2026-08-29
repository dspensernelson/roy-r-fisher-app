"""Unpacking the package, and the second of the two checks.

This is the last thing that happens before anything out of the bucket is
allowed to execute, so every test here asserts the same thing from a different
angle: a package that is not exactly what was built does not get unpacked into
a usable state, and nothing is spawned.

The manifest check is `packaging.verify`, the same one the launcher runs on
every start. A package that would not have started is refused here rather than
after it has been installed over a working one.

Real archives in a temporary folder. That is a narrow mechanic, which is what
synthetic material is allowed to prove: it tests the refusing. It says nothing
about Windows, about Explorer's unzip, or about Mark's machine.
"""
import sys
import zipfile
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))

import packaging  # noqa: E402
import updates  # noqa: E402

TOP = "Roy R. Fisher v0.5.4"


def build_package(tmp_path, version="0.5.4", damage=None):
    """A folder shaped like a built package, with a real manifest over it."""
    root = tmp_path / "built" / TOP
    program = root / packaging.PROGRAM_DIR
    (program / "app" / "server").mkdir(parents=True)
    (program / "python").mkdir()
    (program / "VERSION").write_text(version + "\n", encoding="utf-8")
    (program / "app" / "run_app.py").write_text("# start\n", encoding="utf-8")
    (program / "app" / "update_apply.py").write_text("# apply\n", encoding="utf-8")
    (program / "app" / "server" / "main.py").write_text("# serve\n", encoding="utf-8")
    (program / "python" / "python.exe").write_text("binary\n", encoding="utf-8")
    (root / "Start Roy R. Fisher.bat").write_text("@echo off\r\n", encoding="utf-8")
    (program / packaging.MANIFEST_NAME).write_text(
        packaging.build_manifest(program), encoding="utf-8")
    if damage:
        damage(root, program)
    return root


def make_zip(folder, zip_path, names=None):
    """Archive a folder, or write exactly the entry names given."""
    with zipfile.ZipFile(str(zip_path), "w") as archive:
        if names is not None:
            for name in names:
                archive.writestr(name, "x")
            return zip_path
        for path in sorted(Path(folder).rglob("*")):
            if path.is_file():
                archive.write(str(path),
                              "%s/%s" % (folder.name, path.relative_to(folder).as_posix()))
    return zip_path


@pytest.fixture
def good_zip(tmp_path):
    return make_zip(build_package(tmp_path), tmp_path / "package.zip")


# --- the ordinary case -----------------------------------------------------
def test_a_good_package_unpacks_and_verifies(good_zip):
    package = updates.unpack(good_zip, "0.5.4")
    assert package.name == TOP
    assert (package / packaging.PROGRAM_DIR / "VERSION").is_file()
    packaging.verify(packaging.program_dir(package))


def test_it_unpacks_inside_the_scratch_folder_and_nowhere_else(good_zip):
    package = updates.unpack(good_zip, "0.5.4")
    assert updates.download_dir() in package.parents


# --- archives that are not ours --------------------------------------------
@pytest.mark.parametrize("entry", [
    "../escape.txt",
    TOP + "/../../escape.txt",
    "/absolute.txt",
    TOP + "/sub/../../escape.txt",
    "C:/windows/system32/evil.txt",
    TOP + "\\backslash.txt",
])
def test_an_entry_that_escapes_the_top_folder_is_refused_and_named(tmp_path, entry):
    """Python's own extractor sanitises these quietly. An entry like this means
    the archive is not ours, and the useful thing to do is stop and say
    which."""
    path = make_zip(None, tmp_path / "bad.zip", names=[TOP + "/ok.txt", entry])
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.unpack(path, "0.5.4")
    assert "does not belong" in refused.value.message
    assert entry in refused.value.message


def test_a_second_top_level_folder_is_refused(tmp_path):
    path = make_zip(None, tmp_path / "two.zip",
                    names=[TOP + "/ok.txt", "Somewhere Else/ok.txt"])
    with pytest.raises(updates.UpdateRefused):
        updates.unpack(path, "0.5.4")


def test_an_empty_archive_is_refused(tmp_path):
    path = tmp_path / "empty.zip"
    with zipfile.ZipFile(str(path), "w"):
        pass
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.unpack(path, "0.5.4")
    assert "empty" in refused.value.message


def test_something_that_is_not_a_zip_at_all_is_refused(tmp_path):
    path = tmp_path / "notazip.zip"
    path.write_bytes(b"this is not an archive")
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.unpack(path, "0.5.4")
    assert "could not be opened" in refused.value.message


def test_an_archive_claiming_an_absurd_expansion_is_refused(tmp_path):
    """A small file that says it unpacks to gigabytes. Refused on the claim,
    before a byte of it is written."""
    path = tmp_path / "bomb.zip"
    with zipfile.ZipFile(str(path), "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(TOP + "/big.bin", b"\0" * (8 * 1024 * 1024))
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.unpack(path, "0.5.4")
    assert "far more than it could hold" in refused.value.message


def test_nothing_is_written_when_the_archive_is_refused(tmp_path):
    updates.clear_scratch()
    path = make_zip(None, tmp_path / "bad.zip", names=[TOP + "/ok.txt", "../out.txt"])
    with pytest.raises(updates.UpdateRefused):
        updates.unpack(path, "0.5.4")
    assert not (updates.download_dir() / updates.UNPACKED_DIR).exists()


# --- packages that do not match their own manifest --------------------------
def test_a_missing_file_is_refused_in_the_manifests_own_words(tmp_path):
    def drop_a_file(root, program):
        (program / "app" / "run_app.py").unlink()

    path = make_zip(build_package(tmp_path, damage=drop_a_file), tmp_path / "p.zip")
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.unpack(path, "0.5.4")
    assert "missing a file it needs" in refused.value.message
    assert "run_app.py" in refused.value.message


def test_a_file_of_the_wrong_size_is_refused(tmp_path):
    def truncate(root, program):
        (program / "app" / "run_app.py").write_text("", encoding="utf-8")

    path = make_zip(build_package(tmp_path, damage=truncate), tmp_path / "p.zip")
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.unpack(path, "0.5.4")
    assert "wrong size" in refused.value.message


def test_a_changed_byte_that_keeps_the_size_is_refused(tmp_path):
    """Sizes catch a truncated unzip. The aggregate catches this."""
    def flip(root, program):
        # Exactly as long as "# start\n", so only the aggregate can see it.
        (program / "app" / "run_app.py").write_text("# stavt\n", encoding="utf-8")

    path = make_zip(build_package(tmp_path, damage=flip), tmp_path / "p.zip")
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.unpack(path, "0.5.4")
    assert "do not match the package they came from" in refused.value.message


def test_a_package_with_no_manifest_is_refused(tmp_path):
    def unmanifest(root, program):
        (program / packaging.MANIFEST_NAME).unlink()

    path = make_zip(build_package(tmp_path, damage=unmanifest), tmp_path / "p.zip")
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.unpack(path, "0.5.4")
    assert packaging.MANIFEST_NAME in refused.value.message


def test_a_refused_package_leaves_nothing_unpacked(tmp_path):
    def drop_a_file(root, program):
        (program / "app" / "run_app.py").unlink()

    updates.clear_scratch()
    path = make_zip(build_package(tmp_path, damage=drop_a_file), tmp_path / "p.zip")
    with pytest.raises(updates.UpdateRefused):
        updates.unpack(path, "0.5.4")
    assert not (updates.download_dir() / updates.UNPACKED_DIR).exists()


# --- a package that is not the one that was announced ------------------------
def test_a_package_that_is_not_the_announced_version_is_refused(tmp_path):
    """The bucket said 0.5.4 and the file turned out to be 0.5.9. Something is
    wrong with what was uploaded, and installing it anyway would be guessing."""
    path = make_zip(build_package(tmp_path, version="0.5.9"), tmp_path / "p.zip")
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.unpack(path, "0.5.4")
    assert "said it was version 0.5.4" in refused.value.message
    assert "turned out to be 0.5.9" in refused.value.message

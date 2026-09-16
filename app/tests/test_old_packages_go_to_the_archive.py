"""Every build leaves one package behind, and the rest go to the archive.

Spenser on 2026-09-16, looking at the folder: *"I don't know why there are a
thousand of these damn things. When you make a new one, drag the old one to
the archive."* There were twenty-five versions and 4.2 GB in there, and the
`Archive` folder beside them had been empty since 2026-09-03.

**Moved, never deleted.** A package is the only copy of what was handed over
on a given day, and this project has already lost work to a file that was
tidied. The archive is one drag away and nothing in here removes anything.

**The one that was just built is the one that stays**, because the download
page serves out of this folder by symlink and the whole point of keeping it
loose is that the next person can find it without reading a test.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import package_windows as packager   # noqa: E402


def a_package(folder, version, *, zip_too=True):
    (folder / ("Roy R. Fisher v%s" % version)).mkdir(parents=True)
    if zip_too:
        (folder / ("Roy R. Fisher v%s.zip" % version)).write_text("z")
        (folder / ("Roy R. Fisher v%s.zip.sha256" % version)).write_text("s")


def test_the_old_ones_move_and_the_new_one_stays(tmp_path):
    for v in ("0.6.9", "0.7.5.2", "0.7.6"):
        a_package(tmp_path, v)
    (tmp_path / "latest.json").write_text("{}")

    moved = packager.archive_the_old_packages(tmp_path, "0.7.6")

    loose = sorted(p.name for p in tmp_path.iterdir())
    assert loose == ["Archive", "Roy R. Fisher v0.7.6",
                     "Roy R. Fisher v0.7.6.zip",
                     "Roy R. Fisher v0.7.6.zip.sha256", "latest.json"]
    assert moved == 6


def test_nothing_is_ever_deleted(tmp_path):
    for v in ("0.6.9", "0.7.6"):
        a_package(tmp_path, v)
    before = sum(1 for _ in tmp_path.rglob("*"))

    packager.archive_the_old_packages(tmp_path, "0.7.6")

    assert sum(1 for _ in tmp_path.rglob("*")) == before + 1   # + Archive itself
    assert (tmp_path / "Archive" / "Roy R. Fisher v0.6.9").is_dir()
    assert (tmp_path / "Archive" / "Roy R. Fisher v0.6.9.zip").is_file()


def test_latest_json_stays_because_it_is_what_the_app_reads(tmp_path):
    a_package(tmp_path, "0.7.6")
    (tmp_path / "latest.json").write_text('{"version": "0.7.6"}')

    packager.archive_the_old_packages(tmp_path, "0.7.6")

    assert (tmp_path / "latest.json").read_text() == '{"version": "0.7.6"}'


def test_the_archive_is_not_swept_into_itself(tmp_path):
    a_package(tmp_path, "0.7.6")
    (tmp_path / "Archive").mkdir()
    (tmp_path / "Archive" / "Roy R. Fisher v0.5.0.zip").write_text("old")

    packager.archive_the_old_packages(tmp_path, "0.7.6")

    assert not (tmp_path / "Archive" / "Archive").exists()
    assert (tmp_path / "Archive" / "Roy R. Fisher v0.5.0.zip").is_file()


def test_a_name_already_in_the_archive_does_not_overwrite_the_one_there(tmp_path):
    """Two builds of the same version number happen, and the older file is
    still the record of what was handed over. It keeps its own name."""
    a_package(tmp_path, "0.7.6")
    a_package(tmp_path, "0.7.5.2", zip_too=False)
    (tmp_path / "Archive").mkdir()
    (tmp_path / "Archive" / "Roy R. Fisher v0.7.5.2").mkdir()
    (tmp_path / "Archive" / "Roy R. Fisher v0.7.5.2" / "kept").write_text("first")

    packager.archive_the_old_packages(tmp_path, "0.7.6")

    assert (tmp_path / "Archive" / "Roy R. Fisher v0.7.5.2" / "kept").read_text() == "first"
    assert len(list((tmp_path / "Archive").glob("Roy R. Fisher v0.7.5.2*"))) == 2


def test_a_folder_that_does_not_exist_is_not_an_error(tmp_path):
    assert packager.archive_the_old_packages(tmp_path / "nope", "0.7.6") == 0


def test_it_keeps_the_package_that_was_built_not_the_one_in_VERSION(tmp_path):
    """The two are the same in a release and different whenever `--out` names
    something else. Reading `VERSION` instead of the built package moved a
    package out from under the caller that had just asked for it, and broke
    thirty-one packaging tests on 2026-09-16."""
    a_package(tmp_path, "0.1.0")
    a_package(tmp_path, "0.7.6")

    packager.archive_the_old_packages(tmp_path, "0.1.0")

    assert (tmp_path / "Roy R. Fisher v0.1.0").is_dir()
    assert (tmp_path / "Archive" / "Roy R. Fisher v0.7.6").is_dir()

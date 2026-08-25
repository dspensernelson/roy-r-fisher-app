"""Where a job keeps its photographs, so Mark can be asked which set is the report.

Every job in the corpus holds each shoot twice: full size, and a set the
office shrank by hand. Measured 2026-08-25, the folder names are `Original`,
`Raw pics_`, `Minimized`, `full size`, `Building`, `Used`, `Reduced`,
`3525`/`3575` and `Report Photos_`. Nine conventions across eleven jobs, and a
new helper in Mark's office has just added a tenth. Nothing here reads any of
those names for meaning. It counts what is where and hands the answer to Mark.

A group is the FULL folder path relative to `Photos`, not the immediate child
folder. Mason City decides that: its 50 chosen photographs and its 7 rejected
ones are two folders side by side, both inside `Raw pics_Walmart Mason City
4151 4th St SW`. Grouping by the immediate child would fold them into one
group and hand Mark the seven he threw out.
"""
import hashlib
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import photos  # noqa: E402

from conftest import CORPUS  # noqa: E402


def a_photo(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (120, 90), (60, 110, 160)).save(path)
    return path


def a_job(tmp_path: Path, *relative_paths: str) -> Path:
    job = tmp_path / "DAVENPORT_1 Test Street"
    (job / "Photos").mkdir(parents=True, exist_ok=True)
    for rel in relative_paths:
        a_photo(job / "Photos" / rel)
    return job


def shape(job: Path):
    return [(g["folder"], g["count"]) for g in photos.photo_groups(job)]


# --- the real shapes ------------------------------------------------------
def test_maquoketas_shape(tmp_path):
    """One loose aerial, sixteen raw, sixteen the helper prepared."""
    paths = ["AERIAL.png"]
    paths += ["Raw pics_X/IMG_%04d.jpeg" % n for n in range(559, 575)]
    paths += ["Report Photos_X/%d IMG_%04d.jpeg" % (n - 558, n)
              for n in range(559, 575)]
    job = a_job(tmp_path, *paths)
    assert shape(job) == [("Raw pics_X", 16), ("Report Photos_X", 16), ("", 1)]


def test_mason_citys_nested_shape(tmp_path):
    """Two folders side by side, two levels down. The whole path is the name,
    so the fifty he used and the seven he rejected stay apart."""
    paths = ["Raw pics_W/All report photos used/IMG_%04d.jpeg" % n
             for n in range(1, 51)]
    paths += ["Raw pics_W/Do Not Use/Do Not Use IMG_%04d.jpeg" % n
              for n in range(90, 97)]
    job = a_job(tmp_path, *paths)
    assert shape(job) == [("Raw pics_W/All report photos used", 50),
                          ("Raw pics_W/Do Not Use", 7)]


def test_everything_loose_is_one_group_named_for_the_top(tmp_path):
    job = a_job(tmp_path, "a.jpg", "b.jpg", "c.jpg")
    assert shape(job) == [("", 3)]


def test_the_biggest_group_is_offered_first(tmp_path):
    job = a_job(tmp_path, "Small/one.jpg",
                *["Big/%d.jpg" % n for n in range(9)])
    assert [g["folder"] for g in photos.photo_groups(job)] == ["Big", "Small"]


def test_groups_of_the_same_size_are_ordered_by_name(tmp_path):
    """So the same job asks the same question twice running."""
    job = a_job(tmp_path, "3575/a.jpg", "3525/b.jpg")
    assert [g["folder"] for g in photos.photo_groups(job)] == ["3525", "3575"]


# --- nothing to ask about -------------------------------------------------
def test_an_empty_photos_folder_has_no_groups(tmp_path):
    job = tmp_path / "DAVENPORT_1 Test Street"
    (job / "Photos").mkdir(parents=True)
    assert photos.photo_groups(job) == []


def test_a_job_with_no_photos_folder_at_all_has_no_groups(tmp_path):
    job = tmp_path / "DAVENPORT_1 Test Street"
    job.mkdir()
    assert photos.photo_groups(job) == []


def test_a_folder_holding_no_photographs_is_not_a_group(tmp_path):
    """The built Word file and Thumbs.db sit in these folders. Neither is a
    photograph and neither may produce a group with nothing in it."""
    job = a_job(tmp_path, "one.jpg")
    (job / "Photos" / "Drafts").mkdir()
    (job / "Photos" / "Drafts" / "PHOTOS_Somewhere.docx").write_bytes(b"no")
    assert shape(job) == [("", 1)]


# --- what a group carries -------------------------------------------------
def test_a_group_carries_one_photograph_to_show_him(tmp_path):
    """The question has a thumbnail beside each folder, because the folder
    name alone is not how he recognises his own photographs."""
    job = a_job(tmp_path, "Raw pics_X/one.jpeg")
    group = photos.photo_groups(job)[0]
    assert group["sample"] == "one.jpeg"


def test_the_sample_is_a_photograph_that_is_really_there(tmp_path):
    import jobs
    job = a_job(tmp_path, "Deep/Down/one.jpeg")
    group = photos.photo_groups(job)[0]
    entry = {"file": group["sample"], "folder": group["folder"]}
    assert jobs.photo_path(job, entry).is_file()


# --- against the real corpus, read only -----------------------------------
REAL = pytest.mark.skipif(not CORPUS.is_dir(),
                          reason="the corpus is private and not in this repository")


@REAL
def test_mason_city_really_does_split_fifty_and_seven():
    """Measured 2026-08-25. The reason a group is a full path."""
    job = CORPUS / "MASON CITY_Walmart_4151 4th St SW"
    if not (job / "Photos").is_dir():
        pytest.skip("this job is not in this checkout")
    groups = {g["folder"]: g["count"] for g in photos.photo_groups(job)}
    if not groups:
        pytest.skip("this job's photographs are not in this checkout")
    root = "Raw pics_Walmart Mason City 4151 4th St SW"
    assert groups.get(root + "/All report photos used") == 50
    assert groups.get(root + "/Do Not Use") == 7


@REAL
def test_reading_the_groups_writes_nothing():
    job = CORPUS / "MASON CITY_Walmart_4151 4th St SW"
    if not (job / "Photos").is_dir():
        pytest.skip("this job is not in this checkout")
    def fingerprint():
        found = {}
        for path in sorted((job / "Photos").rglob("*")):
            if path.is_file():
                found[str(path)] = (path.stat().st_size, path.stat().st_mtime)
        return found
    before = fingerprint()
    photos.photo_groups(job)
    assert fingerprint() == before


@REAL
def test_every_corpus_job_offers_at_least_one_group():
    """A job the app can see photographs in always has somewhere to point at,
    so the question can never appear with nothing to answer it."""
    seen = 0
    for job in sorted(p for p in CORPUS.iterdir() if p.is_dir()):
        if not (job / "Photos").is_dir():
            continue
        import jobs
        if jobs.count_photos(job) == 0:
            continue
        seen += 1
        assert photos.photo_groups(job), "%s has photographs and no group" % job.name
    if seen == 0:
        pytest.skip("no corpus job's photographs are in this checkout")

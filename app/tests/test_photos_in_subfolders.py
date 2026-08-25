"""Photographs are found wherever inside Photos they sit.

Spenser found it with a job in flight: the photo screen was empty and there was
nothing on it to say why. The first guess was the file format, because the
camera had changed and everything was now .jpeg. That was wrong. `.jpeg` was
always in PHOTO_EXTS and the check was always case-folded.

The real cause: the app read `Photos` with `iterdir()`, which does not open a
subfolder, and the corpus says that is where the photographs usually are.
Measured across the nine real jobs on 2026-08-24, four of them keep no
photograph directly in Photos at all. Mason City's are two levels down in
`Raw pics_Walmart Mason City 4151 4th St SW/All report photos used`, Brookside's
are split across `3525` and `3575`, Elmore Circle's are in `full size` and
`Building`. Those four jobs showed Mark an empty screen.

It survived every test because every fixture in this suite, and every demo job
the app makes, puts photographs straight into Photos. The app was only ever
tested against folders the app itself had laid out. Even the golden test walked
past it: conftest reaches into Mason City's nested folder by its full path, so
the photographs were read while the thing that could not find them was not.

Why repeats are dropped rather than shown twice. A subfolder is often a second
copy at another size: Bettendorf's `Original` holds the same 71 filenames as the
top of Photos, 4300 E 53rd's `Minimized` holds 11 of its 12, and all 15 of
Elmore's `Building` are already in its `full size`. Listing everything would
have shown Bettendorf 142 photographs when it has 71.

What is deliberately NOT here: any rule about what a folder's name means.
`Do Not Use`, `Used` and `All report photos used` are read as plain folders.
Spenser's `Used` convention is his own and not how the firm will work going
forward, and what should happen to `Do Not Use` is undecided, so the screen
shows Mark which folder each photograph came from and he decides. Guessing at
that in code is how this file's first draft would have hidden seven of Mason
City's photographs without being asked to.
"""
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import jobs  # noqa: E402
import photos  # noqa: E402

from conftest import CORPUS  # noqa: E402


def a_photo(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1000, 750), (60, 110, 160)).save(path)
    return path


def a_job(tmp_path: Path, *relative_paths: str) -> Path:
    """A job whose photographs sit exactly where the arguments say."""
    job = tmp_path / "DAVENPORT_1 Test Street"
    for rel in relative_paths:
        a_photo(job / "Photos" / rel)
    return job


def names(job: Path):
    return [p.name for p in jobs.photo_files(job)]


# --- the defect itself ----------------------------------------------------
def test_a_photograph_in_a_subfolder_is_found(tmp_path):
    job = a_job(tmp_path, "Original/one.jpg")
    assert names(job) == ["one.jpg"]


def test_a_job_with_nothing_at_the_top_of_photos_is_no_longer_empty(tmp_path):
    """Mason City, Brookside, Burlington and Elmore, in one line."""
    job = a_job(tmp_path, "Raw pics_Somewhere/a.jpeg", "Raw pics_Somewhere/b.jpeg")
    assert sorted(names(job)) == ["a.jpeg", "b.jpeg"]
    assert jobs.count_photos(job) == 2


def test_two_levels_down_is_still_found(tmp_path):
    """Mason City's real shape: Raw pics_.../All report photos used."""
    job = a_job(tmp_path, "Raw pics_X/All report photos used/deep.jpeg")
    assert names(job) == ["deep.jpeg"]


def test_photographs_beside_and_below_are_both_listed(tmp_path):
    """Davenport 215 E 37th: 32 loose and 32 different ones in Original."""
    job = a_job(tmp_path, "loose.jpg", "Original/other.jpg")
    assert sorted(names(job)) == ["loose.jpg", "other.jpg"]


def test_jpeg_was_never_the_problem(tmp_path):
    """The first guess, written down so it is not guessed at again."""
    assert ".jpeg" in jobs.PHOTO_EXTS
    job = a_job(tmp_path, "Original/CAMERA.JPEG")
    assert names(job) == ["CAMERA.JPEG"], "the extension check is case-folded"


# --- the same photograph twice --------------------------------------------
def test_a_repeated_filename_is_listed_once(tmp_path):
    job = a_job(tmp_path, "same.jpg", "Original/same.jpg")
    assert names(job) == ["same.jpg"]


def test_the_copy_at_the_top_of_photos_is_the_one_that_wins(tmp_path):
    """Bettendorf's Original is a second copy of the 71 he works from."""
    job = a_job(tmp_path, "same.jpg", "Original/same.jpg")
    assert jobs.photo_folder(job, jobs.photo_files(job)[0]) == ""


def test_a_repeat_across_two_subfolders_is_listed_once(tmp_path):
    """Elmore Circle: every one of Building's 15 is already in full size."""
    job = a_job(tmp_path, "Building/x.jpg", "full size/x.jpg")
    assert names(job) == ["x.jpg"]


def test_a_repeat_in_a_different_case_is_still_a_repeat(tmp_path):
    """Windows would treat these as one file, so the app must too."""
    job = a_job(tmp_path, "shot.jpg", "Original/SHOT.JPG")
    assert names(job) == ["shot.jpg"]


# --- what the manifest records --------------------------------------------
def test_a_new_entry_remembers_its_folder(tmp_path):
    job = a_job(tmp_path, "Raw pics_X/one.jpeg")
    entry = photos.load_manifest(job)["photos"][0]
    assert entry["file"] == "one.jpeg"
    assert entry["folder"] == "Raw pics_X"


def test_a_photograph_at_the_top_records_no_folder_at_all(tmp_path):
    """A job laid out the old way gains no new key, so nothing migrates."""
    job = a_job(tmp_path, "one.jpg")
    assert "folder" not in photos.load_manifest(job)["photos"][0]


def test_an_entry_resolves_to_the_file_it_names(tmp_path):
    job = a_job(tmp_path, "Raw pics_X/All report photos used/one.jpeg")
    entry = photos.load_manifest(job)["photos"][0]
    assert jobs.photo_path(job, entry).is_file()


def test_a_manifest_written_before_this_still_means_the_top_of_photos(tmp_path):
    """No migration: an entry with no folder key means exactly what it did."""
    job = a_job(tmp_path, "one.jpg")
    assert jobs.photo_path(job, {"file": "one.jpg"}) == jobs.photos_dir(job) / "one.jpg"


def test_a_photograph_moved_into_a_subfolder_keeps_its_caption(tmp_path):
    """Reconciliation corrects where it is. It never touches what he wrote."""
    job = a_job(tmp_path, "one.jpg")
    manifest = photos.load_manifest(job)
    manifest["photos"][0]["caption"] = "West elevation"
    manifest["photos"][0]["reviewed"] = True
    photos.save_manifest(job, manifest)

    moved = jobs.photos_dir(job) / "Original"
    moved.mkdir()
    (jobs.photos_dir(job) / "one.jpg").rename(moved / "one.jpg")

    entry = photos.load_manifest(job)["photos"][0]
    assert entry["folder"] == "Original"
    assert entry["caption"] == "West elevation"
    assert entry["reviewed"] is True
    assert jobs.photo_path(job, entry).is_file()


def test_a_photograph_moved_back_up_loses_the_folder_again(tmp_path):
    job = a_job(tmp_path, "Original/one.jpg")
    photos.save_manifest(job, photos.load_manifest(job))
    (jobs.photos_dir(job) / "Original" / "one.jpg").rename(jobs.photos_dir(job) / "one.jpg")
    assert "folder" not in photos.load_manifest(job)["photos"][0]


def test_a_deleted_photograph_is_still_dropped(tmp_path):
    job = a_job(tmp_path, "Original/one.jpg", "Original/two.jpg")
    photos.save_manifest(job, photos.load_manifest(job))
    (jobs.photos_dir(job) / "Original" / "one.jpg").unlink()
    assert [e["file"] for e in photos.load_manifest(job)["photos"]] == ["two.jpg"]


# --- folders that are not folders of his ----------------------------------
def test_the_legacy_thumbnail_cache_is_not_read_as_photographs(tmp_path):
    job = a_job(tmp_path, "one.jpg")
    a_photo(jobs.photos_dir(job) / jobs.PHOTO_SKIP_DIRS.copy().pop() / "cached.jpg")
    assert names(job) == ["one.jpg"]


def test_a_hidden_folder_is_left_alone(tmp_path):
    job = a_job(tmp_path, "one.jpg")
    a_photo(jobs.photos_dir(job) / ".something" / "hidden.jpg")
    assert names(job) == ["one.jpg"]


def test_the_manifest_is_not_a_photograph(tmp_path):
    job = a_job(tmp_path, "Original/one.jpg")
    photos.save_manifest(job, photos.load_manifest(job))
    assert names(job) == ["one.jpg"]


def test_a_document_sitting_in_photos_is_not_a_photograph(tmp_path):
    """Every real Photos folder has the built report sitting in it."""
    job = a_job(tmp_path, "one.jpg")
    (jobs.photos_dir(job) / "PHOTOS_Somewhere.docx").write_bytes(b"not a photo")
    assert names(job) == ["one.jpg"]


# --- the walk cannot be led outside or made to spin ------------------------
def test_a_link_pointing_out_of_photos_is_refused(tmp_path):
    job = a_job(tmp_path, "one.jpg")
    outside = tmp_path / "elsewhere"
    a_photo(outside / "secret.jpg")
    try:
        (jobs.photos_dir(job) / "escape.jpg").symlink_to(outside / "secret.jpg")
    except (OSError, NotImplementedError):
        pytest.skip("this filesystem does not do symlinks")
    assert names(job) == ["one.jpg"]


def test_a_folder_linked_back_to_itself_does_not_spin(tmp_path):
    """Bounded by remembering folders, not by capping depth. A depth cap
    would silently stop listing photographs in a tree that was merely
    nested, which is the failure this whole change exists to end."""
    job = a_job(tmp_path, "Original/one.jpg")
    try:
        (jobs.photos_dir(job) / "Original" / "loop").symlink_to(jobs.photos_dir(job))
    except (OSError, NotImplementedError):
        pytest.skip("this filesystem does not do symlinks")
    assert names(job) == ["one.jpg"]


def test_a_deeply_nested_photograph_is_still_found(tmp_path):
    job = a_job(tmp_path, "a/b/c/d/e/deep.jpg")
    assert names(job) == ["deep.jpg"]


# --- what may be saved ----------------------------------------------------
@pytest.mark.parametrize("folder", [
    "../../elsewhere", "/etc", "Original/../../..", "Original\\..\\..",
])
def test_a_folder_that_climbs_out_is_refused(tmp_path, folder):
    job = a_job(tmp_path, "one.jpg")
    bad = {"photos": [{"file": "one.jpg", "folder": folder, "caption": ""}]}
    assert photos._validate_manifest_shape(job, bad) is not None


def test_a_folder_that_is_not_text_is_refused(tmp_path):
    job = a_job(tmp_path, "one.jpg")
    bad = {"photos": [{"file": "one.jpg", "folder": 7, "caption": ""}]}
    assert photos._validate_manifest_shape(job, bad) is not None


def test_an_ordinary_subfolder_is_allowed(tmp_path):
    job = a_job(tmp_path, "Raw pics_X/All report photos used/one.jpeg")
    assert photos._validate_manifest_shape(job, photos.load_manifest(job)) is None


# --- an upload cannot hide a photograph -----------------------------------
def test_an_upload_does_not_take_a_name_a_nested_photograph_already_has(tmp_path):
    """Without this the upload wins the name, and the walk -- which keeps the
    first of any repeat -- lists the upload and hides the other one."""
    job = a_job(tmp_path, "Original/shot.jpg")
    taken = {p.name.lower() for p in jobs.photo_files(job)}
    assert photos.free_name(jobs.photos_dir(job), "shot.jpg", taken) != "shot.jpg"


def test_free_name_still_behaves_when_nothing_is_taken(tmp_path):
    job = a_job(tmp_path, "one.jpg")
    assert photos.free_name(jobs.photos_dir(job), "two.jpg") == "two.jpg"
    assert photos.free_name(jobs.photos_dir(job), "one.jpg") == "one (2).jpg"


# --- the screen says where a photograph came from -------------------------
SCREEN = Path(__file__).resolve().parents[1] / "web" / "src" / "screens" / "PhotosScreen.jsx"
CSS = Path(__file__).resolve().parents[1] / "web" / "src" / "brand.css"


def test_the_screen_shows_which_folder_a_photograph_came_from():
    """Instead of a rule about folder names. Mark can read `Do Not Use` on the
    tile and cut it; the app does not decide that for him."""
    source = SCREEN.read_text()
    assert "photo-source" in source
    assert "{p.folder &&" in source, "shown only when it came from a subfolder"
    assert 'title={p.folder}' in source, "the whole path is the tooltip"


def test_a_cut_photograph_says_where_it_came_from_too():
    source = SCREEN.read_text()
    assert source.count("photo-source") >= 2


def test_the_label_is_quiet():
    block = CSS.read_text()
    block = block[block.index(".photo-source"):]
    assert "var(--ink-muted)" in block[:block.index("}")]


# --- against the real corpus, read only -----------------------------------
REAL = pytest.mark.skipif(not CORPUS.is_dir(),
                          reason="the corpus is private and not in this repository")

# Measured 2026-08-24. Every number here was counted from the folders
# themselves, and each one that differs from the direct count is a job that
# showed Mark an empty or near-empty screen before this change.
EXPECTED = {
    "MASON CITY_Walmart_4151 4th St SW": (0, 57),
    "DAVENPORT_3525 & 3575 Marquette - Brookside I and II": (0, 128),
    "DAVENPORT_5348 Elmore Circle - 2025": (1, 69),
    "BETTENDORF_St. John Vianney": (71, 71),
    "DAVENPORT_5515 Utica Ridge - 2025 Tax": (42, 61),
    "IOWA COUNTY_2172 M Avenue - 2025 Tax": (31, 92),
    "DAVENPORT_215 E 37th Street - 2026": (32, 64),
    "DAVENPORT_4300 E 53rd Street ROW": (12, 12),
}


@REAL
@pytest.mark.parametrize("job_name,counts", sorted(EXPECTED.items()))
def test_every_real_job_lists_the_photographs_it_has(job_name, counts):
    job = CORPUS / job_name
    if not (job / "Photos").is_dir():
        pytest.skip("this job's Photos folder is not in this checkout")
    was, now = counts
    found = jobs.count_photos(job)
    if found == 0:
        pytest.skip("this job's photographs are not in this checkout")
    assert found == now, "%s: expected %d photographs, found %d" % (job_name, now, found)
    assert found >= was, "no job may list fewer than it did before"


@REAL
def test_bettendorf_is_not_doubled_by_its_original_folder():
    """The reason repeats are dropped: this job would list 142 without it."""
    job = CORPUS / "BETTENDORF_St. John Vianney"
    if not (job / "Photos" / "Original").is_dir():
        pytest.skip("this job's photographs are not in this checkout")
    assert jobs.count_photos(job) == 71


@REAL
def test_nothing_in_the_corpus_is_written_to():
    """This whole section reads. If it ever writes, that is the bug."""
    job = CORPUS / "MASON CITY_Walmart_4151 4th St SW"
    if not (job / "Photos").is_dir():
        pytest.skip("this job is not in this checkout")
    before = {p: p.stat().st_mtime for p in (job / "Photos").rglob("*")}
    jobs.photo_files(job)
    jobs.count_photos(job)
    after = {p: p.stat().st_mtime for p in (job / "Photos").rglob("*")}
    assert before == after

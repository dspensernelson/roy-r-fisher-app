"""What the app says is in a job folder must be what is in it.

The old readiness scan decided a file's folder by testing the folder's name
against the whole parent path as a string, so a job stored under a path
containing "maps" matched Maps everywhere. These tests pin the replacement:
a folder is a direct child directory of the job, identified by its exact
name off the disk, and nothing is ever inferred from a path fragment.

Synthetic folders here prove these mechanics and nothing else. No claim
about Mark's real folder structures rests on them.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import inventory  # noqa: E402
import jobs  # noqa: E402


def make_job(home: Path, name: str = "JOB1") -> Path:
    job = home / name
    for folder in jobs.MARK_FOLDERS:
        (job / folder).mkdir(parents=True)
    return job


def files_in(result, folder_name):
    for group in ("typical", "other"):
        for row in result[group]:
            if row["folder"] == folder_name:
                return row
    return None


def test_typical_folders_are_marks_own_eight_by_exact_name(tmp_path):
    job = make_job(tmp_path)
    result = inventory.read_job(job)
    assert [r["folder"] for r in result["typical"]] == jobs.MARK_FOLDERS
    assert result["other"] == []


def test_a_folder_mark_invented_is_shown_not_hidden(tmp_path):
    job = make_job(tmp_path)
    (job / "Site Visit 8-14").mkdir()
    (job / "Site Visit 8-14" / "notes.pdf").write_bytes(b"x")
    result = inventory.read_job(job)
    other = [r["folder"] for r in result["other"]]
    assert other == ["Site Visit 8-14"]
    assert files_in(result, "Site Visit 8-14")["count"] == 1


def test_a_nested_file_belongs_to_its_top_level_folder(tmp_path):
    job = make_job(tmp_path)
    (job / "Maps" / "2025").mkdir()
    (job / "Maps" / "2025" / "plat.pdf").write_bytes(b"x")
    row = files_in(inventory.read_job(job), "Maps")
    assert row["count"] == 1
    entry = row["files"][0]
    assert entry["name"] == "plat.pdf"
    assert entry["rel"] == "Maps/2025/plat.pdf"
    assert entry["within"] == "2025"


def test_a_file_directly_in_the_folder_reports_no_sub_location(tmp_path):
    job = make_job(tmp_path)
    (job / "Maps" / "plat.pdf").write_bytes(b"x")
    entry = files_in(inventory.read_job(job), "Maps")["files"][0]
    assert entry["rel"] == "Maps/plat.pdf"
    assert entry["within"] == ""


def test_an_exact_name_never_swallows_a_similar_folder(tmp_path):
    """The regression the old substring matching produced."""
    job = make_job(tmp_path)
    (job / "Site Maps").mkdir()
    (job / "Site Maps" / "aerial.jpg").write_bytes(b"x")
    (job / "Maps" / "plat.pdf").write_bytes(b"x")
    result = inventory.read_job(job)
    assert [f["name"] for f in files_in(result, "Maps")["files"]] == ["plat.pdf"]
    assert [f["name"] for f in files_in(result, "Site Maps")["files"]] == ["aerial.jpg"]


def test_the_jobs_own_path_never_creates_a_folder(tmp_path):
    """A job living under a folder called Maps must not grow a Maps row from
    its path. Only a real directory inside the job counts."""
    home = tmp_path / "Maps"
    home.mkdir()
    job = home / "DAVENPORT_Maps Road - 2026"
    (job / "Photos").mkdir(parents=True)
    (job / "Photos" / "IMG_1.jpg").write_bytes(b"x")
    result = inventory.read_job(job)
    names = [r["folder"] for r in result["typical"] + result["other"]]
    assert names == ["Photos"]


def test_hidden_and_noise_and_thumbs_are_not_listed(tmp_path):
    job = make_job(tmp_path)
    (job / "Photos" / "IMG_1.jpg").write_bytes(b"x")
    (job / "Photos" / ".DS_Store").write_bytes(b"x")
    (job / "Photos" / "Thumbs.db").write_bytes(b"x")
    (job / "Photos" / "desktop.ini").write_bytes(b"x")
    (job / "Photos" / ".hidden.pdf").write_bytes(b"x")
    (job / "Photos" / ".rrf-thumbs").mkdir()
    (job / "Photos" / ".rrf-thumbs" / "IMG_1.jpg.jpg").write_bytes(b"x")
    row = files_in(inventory.read_job(job), "Photos")
    assert [f["name"] for f in row["files"]] == ["IMG_1.jpg"]
    assert row["count"] == 1


def test_the_photo_manifest_is_a_real_file_and_is_shown(tmp_path):
    """It is a file in his folder. Hiding it would be the app deciding what
    he is allowed to see."""
    job = make_job(tmp_path)
    (job / "Photos" / "photo-manifest.json").write_text("{}")
    row = files_in(inventory.read_job(job), "Photos")
    assert [f["name"] for f in row["files"]] == ["photo-manifest.json"]


def test_loose_files_at_the_job_root_are_returned_separately(tmp_path):
    job = make_job(tmp_path)
    (job / "Valuation.xlsm").write_bytes(b"x")
    (job / "job-brief.md").write_text("# Job Brief\n")
    result = inventory.read_job(job)
    assert sorted(f["name"] for f in result["root_files"]) == [
        "Valuation.xlsm", "job-brief.md"]
    assert result["root_files"][0]["within"] == ""


def test_the_count_stays_true_when_the_list_is_capped(tmp_path):
    job = make_job(tmp_path)
    for i in range(inventory.FILE_LIMIT + 5):
        (job / "Comps" / f"comp {i:03d}.pdf").write_bytes(b"x")
    row = files_in(inventory.read_job(job), "Comps")
    assert row["count"] == inventory.FILE_LIMIT + 5
    assert len(row["files"]) == inventory.FILE_LIMIT
    assert row["truncated"] is True


def test_a_small_folder_is_not_marked_truncated(tmp_path):
    job = make_job(tmp_path)
    (job / "Comps" / "comp.pdf").write_bytes(b"x")
    assert files_in(inventory.read_job(job), "Comps")["truncated"] is False


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits only")
def test_an_unreadable_folder_says_so_and_is_never_called_empty(tmp_path):
    job = make_job(tmp_path)
    shut = job / "Financials"
    (shut / "rent roll.pdf").write_bytes(b"x")
    shut.chmod(0o000)
    try:
        row = files_in(inventory.read_job(job), "Financials")
        assert row["unreadable"] is True
        assert row["count"] is None
        assert row["files"] == []
    finally:
        shut.chmod(0o700)


def _symlink_or_skip(link: Path, target: Path):
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("this machine will not create symlinks")


def test_a_shortcut_to_a_file_is_named_but_never_followed(tmp_path):
    job = make_job(tmp_path)
    outside = tmp_path / "somewhere else.pdf"
    outside.write_bytes(b"secret")
    _symlink_or_skip(job / "Maps" / "link.pdf", outside)
    entry = files_in(inventory.read_job(job), "Maps")["files"][0]
    assert entry["name"] == "link.pdf"
    assert entry["kind"] == "shortcut"


def test_a_shortcut_to_a_folder_is_never_traversed(tmp_path):
    job = make_job(tmp_path)
    outside = tmp_path / "other job"
    outside.mkdir()
    (outside / "not ours.pdf").write_bytes(b"x")
    _symlink_or_skip(job / "Borrowed", outside)
    result = inventory.read_job(job)
    row = files_in(result, "Borrowed")
    assert row["kind"] == "shortcut"
    assert row["files"] == []
    assert row["count"] is None
    every_name = [f["name"]
                  for group in ("typical", "other")
                  for r in result[group] for f in r["files"]]
    assert "not ours.pdf" not in every_name


def test_a_shortcut_loop_cannot_hang_the_scan(tmp_path):
    job = make_job(tmp_path)
    _symlink_or_skip(job / "Maps" / "loop", job / "Maps")
    row = files_in(inventory.read_job(job), "Maps")
    assert [f["kind"] for f in row["files"]] == ["shortcut"]

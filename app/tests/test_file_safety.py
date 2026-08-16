"""Mark's files are his. The app reads the directory and nothing else.

This is the test that matters most in the classification slice. It takes a
full fingerprint of a job folder, every path, size, modification time and
the bytes of every file, runs everything the app can do to that job, and
demands the fingerprint come back identical.

If this fails, stop. It is a finding, not a test to loosen.
"""
import hashlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import classify  # noqa: E402
import inventory  # noqa: E402
import jobs  # noqa: E402


def fingerprint(job: Path) -> list:
    """Every path under the job, with what it is and exactly what is in it.

    The test may open files. The app may not. That asymmetry is the point.
    """
    out = []
    for path in sorted(job.rglob("*"), key=lambda p: str(p)):
        rel = path.relative_to(job).as_posix()
        if path.is_symlink():
            out.append((rel, "link", os.readlink(str(path)), None, None))
        elif path.is_dir():
            out.append((rel, "dir", None, None, None))
        else:
            info = path.stat()
            out.append((rel, "file", hashlib.sha256(path.read_bytes()).hexdigest(),
                        info.st_size, info.st_mtime_ns))
    return out


@pytest.fixture
def job(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_CLASSIFY_FILE", str(tmp_path / "answers.json"))
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path / "home"))
    place = tmp_path / "home" / "DAVENPORT_215 E 37th Street - 2026"
    for folder in jobs.MARK_FOLDERS:
        (place / folder).mkdir(parents=True)
    (place / "Maps" / "plat 2025 final.pdf").write_bytes(b"%PDF-1.4 plat")
    (place / "Maps" / "2025").mkdir()
    (place / "Maps" / "2025" / "aerial.jpg").write_bytes(b"\xff\xd8 aerial")
    (place / "Photos" / "IMG_5100.jpg").write_bytes(b"\xff\xd8 photo")
    (place / "Photos" / "photo-manifest.json").write_text('{"photos": []}')
    (place / "Photos" / ".rrf-thumbs").mkdir()
    (place / "Photos" / ".rrf-thumbs" / "IMG_5100.jpg.jpg").write_bytes(b"thumb")
    (place / "Photos" / ".DS_Store").write_bytes(b"noise")
    (place / "Site Visit 8-14").mkdir()
    (place / "Site Visit 8-14" / "notes.pdf").write_bytes(b"notes")
    (place / "Valuation.xlsm").write_bytes(b"PK workbook")
    (place / "job-brief.md").write_text("# Job Brief\n")
    return place


def test_reading_a_job_changes_nothing_in_it(job):
    before = fingerprint(job)
    inventory.read_job(job)
    inventory.read_job(job)
    assert fingerprint(job) == before


def test_the_whole_classification_cycle_changes_nothing_in_it(job):
    before = fingerprint(job)

    classify.set_label(job, "Maps/plat 2025 final.pdf", "Plat map")
    classify.set_label(job, "Maps/2025/aerial.jpg", "Aerial photo")
    classify.set_label(job, "Photos/IMG_5100.jpg", "Subject photograph")
    classify.set_label(job, "Valuation.xlsm", "Valuation workbook")
    # Change one, remove another, read every verdict.
    classify.set_label(job, "Maps/2025/aerial.jpg", "Neighborhood map")
    classify.remove_label(job, "Photos/IMG_5100.jpg")
    for rel in classify.for_job(job):
        classify.state_of(job, rel)
    inventory.read_job(job)

    assert fingerprint(job) == before


def test_nothing_the_app_owns_is_written_inside_the_job(job):
    classify.set_label(job, "Maps/plat 2025 final.pdf", "Plat map")
    names = {p.name for p in job.rglob("*")}
    assert classify.STORE_NAME not in names
    assert not [n for n in names if n.endswith(".writing")]
    # The store is real, and it is somewhere else entirely.
    assert classify.store_file().is_file()
    assert job not in classify.store_file().parents


def test_a_refused_classification_leaves_the_job_untouched(job):
    before = fingerprint(job)
    with pytest.raises(ValueError):
        classify.set_label(job, "Maps/plat 2025 final.pdf", "Building sketch")
    with pytest.raises(LookupError):
        classify.set_label(job, "Photos/.rrf-thumbs/IMG_5100.jpg.jpg",
                           "Subject photograph")
    with pytest.raises(LookupError):
        classify.set_label(job, "../escape.pdf", "Deed")
    assert fingerprint(job) == before
    assert classify.for_job(job) == {}


def test_a_shortcut_out_of_the_job_is_never_opened_or_followed(tmp_path, job):
    secret = tmp_path / "not marks.pdf"
    secret.write_bytes(b"someone else's file")
    try:
        (job / "Maps" / "borrowed.pdf").symlink_to(secret)
    except (OSError, NotImplementedError):
        pytest.skip("this machine will not create symlinks")
    outside_before = fingerprint(tmp_path)
    result = inventory.read_job(job)
    maps = [r for r in result["typical"] if r["folder"] == "Maps"][0]
    link = [f for f in maps["files"] if f["name"] == "borrowed.pdf"][0]
    assert link["kind"] == "shortcut"
    with pytest.raises(LookupError):
        classify.set_label(job, "Maps/borrowed.pdf", "Plat map")
    assert fingerprint(tmp_path) == outside_before

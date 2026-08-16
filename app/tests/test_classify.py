"""What Mark says a file is, remembered outside his folders.

A classification is something the app knows, not something in his job, so
it lives in the app's own file in his home folder. These tests pin that,
and pin the three things the app may say about a classified file: the
source is present, it changed, or it is gone.

Synthetic folders here prove these mechanics and nothing else.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import classify  # noqa: E402


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_CLASSIFY_FILE", str(tmp_path / "marks-answers.json"))
    return tmp_path / "marks-answers.json"


def make_job(tmp_path, name="JOB1") -> Path:
    job = tmp_path / name
    (job / "Maps").mkdir(parents=True)
    (job / "Maps" / "plat.pdf").write_bytes(b"a plat")
    return job


def test_the_nine_approved_labels_and_nothing_else(store):
    assert classify.LABELS == (
        "Engagement letter",
        "Deed",
        "Assessor or tax record",
        "Subject photograph",
        "Plat map",
        "Neighborhood map",
        "Aerial photo",
        "Comparable sale document",
        "Valuation workbook",
    )


def test_a_label_outside_the_list_is_refused(store, tmp_path):
    job = make_job(tmp_path)
    with pytest.raises(ValueError):
        classify.set_label(job, "Maps/plat.pdf", "Building sketch")
    with pytest.raises(ValueError):
        classify.set_label(job, "Maps/plat.pdf", "whatever Mark typed")
    assert classify.for_job(job) == {}


def test_a_file_that_is_not_there_cannot_be_classified(store, tmp_path):
    job = make_job(tmp_path)
    with pytest.raises(LookupError):
        classify.set_label(job, "Maps/imaginary.pdf", "Plat map")


def test_a_classification_survives_a_restart(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    # Nothing cached: a fresh read of the file on disk, as the next start does.
    saved = classify.for_job(job)
    assert saved["Maps/plat.pdf"]["label"] == "Plat map"
    assert json.loads(store.read_text())["jobs"]


def test_the_record_lives_outside_the_job_folder(store, tmp_path):
    job = make_job(tmp_path)
    before = sorted(p.relative_to(job).as_posix() for p in job.rglob("*"))
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    after = sorted(p.relative_to(job).as_posix() for p in job.rglob("*"))
    assert before == after
    assert store.is_file()


def test_changing_a_label_replaces_it_rather_than_appending(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    classify.set_label(job, "Maps/plat.pdf", "Aerial photo")
    saved = classify.for_job(job)
    assert len(saved) == 1
    assert saved["Maps/plat.pdf"]["label"] == "Aerial photo"


def test_removing_one_record_leaves_the_others_alone(store, tmp_path):
    job = make_job(tmp_path)
    (job / "Maps" / "aerial.jpg").write_bytes(b"an aerial")
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    classify.set_label(job, "Maps/aerial.jpg", "Aerial photo")
    classify.remove_label(job, "Maps/plat.pdf")
    saved = classify.for_job(job)
    assert list(saved) == ["Maps/aerial.jpg"]


def test_two_jobs_keep_their_own_answers(store, tmp_path):
    one = make_job(tmp_path, "JOB1")
    two = make_job(tmp_path, "JOB2")
    classify.set_label(one, "Maps/plat.pdf", "Plat map")
    classify.set_label(two, "Maps/plat.pdf", "Aerial photo")
    assert classify.for_job(one)["Maps/plat.pdf"]["label"] == "Plat map"
    assert classify.for_job(two)["Maps/plat.pdf"]["label"] == "Aerial photo"
    classify.remove_label(one, "Maps/plat.pdf")
    assert classify.for_job(one) == {}
    assert classify.for_job(two)["Maps/plat.pdf"]["label"] == "Aerial photo"


def test_an_untouched_file_reads_present(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    assert classify.state_of(job, "Maps/plat.pdf") == "present"


def test_a_renamed_file_reads_missing_and_never_present(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    (job / "Maps" / "plat.pdf").rename(job / "Maps" / "plat final.pdf")
    assert classify.state_of(job, "Maps/plat.pdf") == "missing"
    # The record is kept, so Mark can still see it and clear it himself.
    assert classify.for_job(job)["Maps/plat.pdf"]["label"] == "Plat map"


def test_a_different_file_at_the_same_name_reads_changed(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    (job / "Maps" / "plat.pdf").write_bytes(b"a completely different document")
    assert classify.state_of(job, "Maps/plat.pdf") == "changed"


def test_a_record_can_be_removed_after_its_file_is_gone(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    (job / "Maps" / "plat.pdf").unlink()
    classify.remove_label(job, "Maps/plat.pdf")
    assert classify.for_job(job) == {}


def test_a_failed_write_does_not_destroy_what_was_already_saved(store, tmp_path):
    job = make_job(tmp_path)
    (job / "Maps" / "aerial.jpg").write_bytes(b"an aerial")
    classify.set_label(job, "Maps/plat.pdf", "Plat map")

    def explode(*args, **kwargs):
        raise OSError("disk went away")

    # Its own context on purpose. Undoing the shared monkeypatch here would
    # also undo the fixture's RRF_CLASSIFY_FILE and point the next line at
    # the real store in the home folder.
    with pytest.MonkeyPatch.context() as broken:
        broken.setattr(classify.json, "dump", explode)
        with pytest.raises(OSError):
            classify.set_label(job, "Maps/aerial.jpg", "Aerial photo")

    saved = classify.for_job(job)
    assert saved["Maps/plat.pdf"]["label"] == "Plat map"
    assert "Maps/aerial.jpg" not in saved
    assert not list(store.parent.glob("*.writing"))


def test_an_unreadable_store_is_never_repaired_or_guessed_at(store, tmp_path):
    job = make_job(tmp_path)
    store.write_text("{ not json")
    assert classify.for_job(job) == {}

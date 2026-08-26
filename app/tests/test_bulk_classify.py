"""Many files take one label in one action.

Mark classifies one file at a time: open the folder, click Classify on a row,
pick a label. Two clicks each. Mason City keeps 57 photographs in one folder,
so telling the app what they are is 114 clicks, and that is the whole reason
this exists.

One write, however many files. Fifty-seven separate saves is fifty-seven
chances to be interrupted halfway through, and the store holds every answer he
has ever given about every job.

A batch may half-succeed on purpose. Ticking sixteen files where two are PDFs
and picking Subject photograph labels the fourteen that can take it and refuses
the two. Refusing all sixteen because of two punishes him for the app's own
rule. The refusal wording is the one the single-file path already uses, so the
two can never give different reasons for the same thing.
"""
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import classify  # noqa: E402

SUBJECT = "Subject photograph"


def a_job(tmp_path: Path, *relative_paths: str) -> Path:
    job = tmp_path / "DAVENPORT_1 Test Street"
    for rel in relative_paths:
        path = job / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"pretend contents")
    return job


def photos_named(n: int, folder: str = "Photos"):
    return ["%s/IMG_%04d.jpeg" % (folder, i) for i in range(1, n + 1)]


def fingerprint(folder: Path) -> dict:
    found = {}
    for path in sorted(Path(folder).rglob("*")):
        if path.is_file():
            found[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def labels_in(job: Path) -> dict:
    return {rel: rec["label"] for rel, rec in classify.for_job(job).items()}


# --- the case it exists for -----------------------------------------------
def test_a_folder_of_photographs_takes_one_label_in_one_call(tmp_path):
    """Mason City's shape, in one line, which is 114 clicks today."""
    rels = photos_named(57)
    job = a_job(tmp_path, *rels)
    answer = classify.set_labels(job, rels, SUBJECT)
    assert len(answer["applied"]) == 57
    assert answer["refused"] == []
    assert set(labels_in(job)) == set(rels)


def test_every_record_looks_exactly_like_a_single_one(tmp_path):
    """Bulk is a way of saying it, not a different kind of answer."""
    rels = photos_named(2)
    job = a_job(tmp_path, *rels)
    classify.set_labels(job, rels, SUBJECT)
    one = classify.for_job(job)[rels[0]]
    assert one["label"] == SUBJECT
    assert set(one) == {"label", "confirmed_at", "size", "mtime"}


def test_the_store_is_written_once_however_many_files(tmp_path, monkeypatch):
    """Not fifty-seven times. Every answer he has ever given is in this file."""
    rels = photos_named(57)
    job = a_job(tmp_path, *rels)
    writes = []
    real = classify.state.write_json
    monkeypatch.setattr(classify.state, "write_json",
                        lambda path, data: (writes.append(path), real(path, data))[1])
    classify.set_labels(job, rels, SUBJECT)
    assert len(writes) == 1


def test_all_nine_labels_work_not_only_photographs(tmp_path):
    for label in classify.LABELS:
        rels = ["Comps/one.pdf", "Comps/two.pdf"]
        job = a_job(tmp_path / label.replace(" ", "_"), *rels)
        answer = classify.set_labels(job, rels, label)
        if label == SUBJECT:
            assert answer["applied"] == []      # PDFs, refused with a reason
        else:
            assert len(answer["applied"]) == 2, label


# --- a batch may half succeed ---------------------------------------------
def test_the_ones_that_can_take_it_do_and_the_rest_are_refused(tmp_path):
    good = photos_named(14)
    bad = ["Photos/Signed Engagement Letter.pdf", "Photos/notes.docx"]
    job = a_job(tmp_path, *(good + bad))
    answer = classify.set_labels(job, good + bad, SUBJECT)
    assert sorted(answer["applied"]) == sorted(good)
    assert [r["file"] for r in answer["refused"]] == bad


def test_a_refusal_carries_the_same_words_the_single_path_uses(tmp_path):
    rel = "Photos/Signed Engagement Letter.pdf"
    job = a_job(tmp_path, rel, "Photos/one.jpeg")
    answer = classify.set_labels(job, [rel, "Photos/one.jpeg"], SUBJECT)
    assert answer["refused"][0]["reason"] == classify.refusal(job, rel, SUBJECT)
    assert answer["refused"][0]["reason"] == (
        "That is a PDF. Only photographs go on the photo pages.")


def test_nothing_is_recorded_for_a_refused_file(tmp_path):
    """A record that does nothing is worse than no record."""
    rel = "Photos/Signed Engagement Letter.pdf"
    job = a_job(tmp_path, rel, "Photos/one.jpeg")
    classify.set_labels(job, [rel, "Photos/one.jpeg"], SUBJECT)
    assert rel not in labels_in(job)


def test_a_whole_batch_can_be_refused_without_raising(tmp_path):
    rels = ["Photos/a.pdf", "Photos/b.pdf"]
    job = a_job(tmp_path, *rels)
    answer = classify.set_labels(job, rels, SUBJECT)
    assert answer["applied"] == []
    assert len(answer["refused"]) == 2
    assert labels_in(job) == {}


# --- files the app cannot see ---------------------------------------------
def test_a_file_that_is_not_there_is_refused_not_recorded(tmp_path):
    job = a_job(tmp_path, "Photos/one.jpeg")
    answer = classify.set_labels(job, ["Photos/one.jpeg", "Photos/gone.jpeg"],
                                 SUBJECT)
    assert answer["applied"] == ["Photos/one.jpeg"]
    assert answer["refused"][0]["file"] == "Photos/gone.jpeg"
    assert "gone.jpeg" not in str(labels_in(job))


# --- a bad label is not something one file can be wrong about --------------
def test_a_label_outside_the_nine_raises_before_anything_is_written(tmp_path):
    rels = photos_named(3)
    job = a_job(tmp_path, *rels)
    with pytest.raises(ValueError):
        classify.set_labels(job, rels, "Whatever I like")
    assert labels_in(job) == {}


def test_an_empty_list_changes_nothing(tmp_path):
    job = a_job(tmp_path, "Photos/one.jpeg")
    classify.set_labels(job, ["Photos/one.jpeg"], "Deed")
    answer = classify.set_labels(job, [], SUBJECT)
    assert answer == {"applied": [], "refused": []}
    assert labels_in(job) == {"Photos/one.jpeg": "Deed"}


# --- it replaces, the way Change already does -----------------------------
def test_a_file_already_classified_is_replaced(tmp_path):
    rels = photos_named(2)
    job = a_job(tmp_path, *rels)
    classify.set_labels(job, rels, "Deed")
    classify.set_labels(job, rels, SUBJECT)
    assert set(labels_in(job).values()) == {SUBJECT}


# --- one job's answers are one job's --------------------------------------
def test_another_jobs_records_are_untouched(tmp_path):
    mine = a_job(tmp_path / "here", *photos_named(2))
    theirs = a_job(tmp_path / "there", "Photos/other.jpeg")
    classify.set_labels(theirs, ["Photos/other.jpeg"], "Deed")
    classify.set_labels(mine, photos_named(2), SUBJECT)
    assert labels_in(theirs) == {"Photos/other.jpeg": "Deed"}


def test_a_files_own_earlier_answer_in_the_same_job_survives(tmp_path):
    job = a_job(tmp_path, "Photos/one.jpeg", "Comps/deed.pdf")
    classify.set_labels(job, ["Comps/deed.pdf"], "Deed")
    classify.set_labels(job, ["Photos/one.jpeg"], SUBJECT)
    assert labels_in(job) == {"Comps/deed.pdf": "Deed",
                              "Photos/one.jpeg": SUBJECT}


# --- nothing of Mark's is touched -----------------------------------------
def test_nothing_is_written_inside_the_job_folder(tmp_path):
    rels = photos_named(20)
    job = a_job(tmp_path, *rels)
    before = fingerprint(job)
    classify.set_labels(job, rels, SUBJECT)
    assert fingerprint(job) == before

"""Saying a thing cannot be done, rather than writing it down and doing nothing.

Spenser marked a signed engagement letter a subject photograph. The app
recorded it, put "Subject photograph, confirmed by you" on the row, and did
nothing whatever, because a PDF is not a photograph and because it was sitting
in Subject Information rather than in Photos. He gave an instruction, the
screen said it had been taken, and nothing had.

A record that does nothing is worse than no record, so the answer is a refusal
with the reason in it and nothing written down.

The refusal is only ever about `Subject photograph`, which is the one label
that decides what gets built. What a file is in every other sense is his to
say, and the app does not argue with him about it.
"""
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


# --- a thing that is not a photograph -------------------------------------
def test_a_pdf_is_refused_and_the_sentence_names_it(tmp_path):
    job = a_job(tmp_path, "Subject Information/Signed Engagement Letter.pdf")
    said = classify.refusal(job, "Subject Information/Signed Engagement Letter.pdf",
                            SUBJECT)
    assert said == "That is a PDF. Only photographs go on the photo pages."


def test_a_word_document_is_refused(tmp_path):
    job = a_job(tmp_path, "Photos/PHOTOS_Somewhere.docx")
    said = classify.refusal(job, "Photos/PHOTOS_Somewhere.docx", SUBJECT)
    assert said == "That is a Word document. Only photographs go on the photo pages."


def test_a_workbook_is_refused(tmp_path):
    job = a_job(tmp_path, "Photos/numbers.xlsm")
    assert "spreadsheet" in classify.refusal(job, "Photos/numbers.xlsm", SUBJECT)


def test_anything_else_is_refused_without_pretending_to_name_it(tmp_path):
    job = a_job(tmp_path, "Photos/notes.txt")
    said = classify.refusal(job, "Photos/notes.txt", SUBJECT)
    assert said == "That is not a photograph. Only photographs go on the photo pages."


def test_the_file_type_is_read_without_case_mattering(tmp_path):
    job = a_job(tmp_path, "Photos/LETTER.PDF")
    assert "a PDF" in classify.refusal(job, "Photos/LETTER.PDF", SUBJECT)


# --- a photograph in the wrong place --------------------------------------
def test_a_photograph_outside_photos_is_refused_and_says_where_it_is(tmp_path):
    job = a_job(tmp_path, "Maps/aerial.png")
    said = classify.refusal(job, "Maps/aerial.png", SUBJECT)
    assert said == ("That photograph is in Maps. The photo pages are built from "
                    "the job's Photos folder.")


def test_a_photograph_loose_in_the_job_folder_is_refused(tmp_path):
    job = a_job(tmp_path, "stray.jpg")
    said = classify.refusal(job, "stray.jpg", SUBJECT)
    assert "the job folder" in said
    assert "Photos folder" in said


# --- what is allowed ------------------------------------------------------
def test_a_photograph_in_photos_is_allowed(tmp_path):
    job = a_job(tmp_path, "Photos/one.jpeg")
    assert classify.refusal(job, "Photos/one.jpeg", SUBJECT) is None


def test_a_photograph_in_a_subfolder_of_photos_is_allowed(tmp_path):
    job = a_job(tmp_path, "Photos/Raw pics_X/one.jpeg")
    assert classify.refusal(job, "Photos/Raw pics_X/one.jpeg", SUBJECT) is None


def test_every_kind_of_photograph_the_app_reads_is_allowed(tmp_path):
    import jobs
    for ext in sorted(jobs.PHOTO_EXTS):
        job = a_job(tmp_path, "Photos/one%s" % ext)
        assert classify.refusal(job, "Photos/one%s" % ext, SUBJECT) is None, ext


# --- every other label is his business ------------------------------------
@pytest.mark.parametrize("label", [l for l in classify.LABELS if l != SUBJECT])
def test_no_other_label_is_ever_argued_with(tmp_path, label):
    """A PDF really is an engagement letter. The app has no business refusing
    what a file is; it refuses only a claim it cannot act on."""
    job = a_job(tmp_path, "Subject Information/Signed Engagement Letter.pdf")
    assert classify.refusal(
        job, "Subject Information/Signed Engagement Letter.pdf", label) is None


# --- and nothing is written down ------------------------------------------
def _client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import main
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path))
    return TestClient(main.create_app())


def test_the_route_refuses_and_says_why(tmp_path, monkeypatch):
    a_job(tmp_path, "Subject Information/Signed Engagement Letter.pdf")
    client = _client(tmp_path, monkeypatch)
    answer = client.put(
        "/api/jobs/DAVENPORT_1 Test Street/classification",
        json={"file": "Subject Information/Signed Engagement Letter.pdf",
              "label": SUBJECT})
    assert answer.status_code == 400
    assert answer.json()["detail"] == (
        "That is a PDF. Only photographs go on the photo pages.")


def test_a_refused_classification_is_not_recorded(tmp_path, monkeypatch):
    """The whole point. The old behaviour wrote it down and did nothing."""
    job = a_job(tmp_path, "Subject Information/Signed Engagement Letter.pdf")
    client = _client(tmp_path, monkeypatch)
    client.put("/api/jobs/DAVENPORT_1 Test Street/classification",
               json={"file": "Subject Information/Signed Engagement Letter.pdf",
                     "label": SUBJECT})
    assert classify.for_job(job) == {}


def test_the_same_file_can_still_be_called_what_it_is(tmp_path, monkeypatch):
    job = a_job(tmp_path, "Subject Information/Signed Engagement Letter.pdf")
    client = _client(tmp_path, monkeypatch)
    answer = client.put(
        "/api/jobs/DAVENPORT_1 Test Street/classification",
        json={"file": "Subject Information/Signed Engagement Letter.pdf",
              "label": "Engagement letter"})
    assert answer.status_code == 200
    assert classify.for_job(job)[
        "Subject Information/Signed Engagement Letter.pdf"]["label"] == "Engagement letter"

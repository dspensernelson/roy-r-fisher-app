"""The Description of Improvements endpoints.

Synthetic files and a temporary jobs folder. That proves the mechanics only:
what is offered, what is confined, what is saved and where, and that nothing
is sent until Mark says so. Claims about Mark's real documents live in
test_improvements_sources.py, which reads the real ones.

No model is called anywhere here. The two that would are refused for want of a
key, which is itself the behaviour being checked.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import improvements_routes  # noqa: E402
from main import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / "jobs"
    job = home / "A job"
    (job / "Subject Information").mkdir(parents=True)
    (job / "Transcripts").mkdir(parents=True)
    (job / "Comps" / "ID 1 somewhere else").mkdir(parents=True)
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    monkeypatch.setenv("RRF_IMPROVEMENTS_FILE", str(tmp_path / "store.json"))
    monkeypatch.setenv("RRF_KEY_FILE", str(tmp_path / "nokey.json"))
    yield TestClient(create_app()), job




def test_a_job_with_neither_source_is_not_ready(client):
    api, job = client
    body = api.get("/api/jobs/A job/improvements/sources").json()
    assert body["ready"] is False
    assert body["cards"] == [] and body["transcripts"] == []


def test_a_comparable_sale_card_is_never_offered(client):
    """A comp's record card describes a different building. Offering one is how
    another building's walls reach Mark's report."""
    api, job = client
    (job / "Comps" / "ID 1 somewhere else" / "PRC_Some Other Place.pdf").write_bytes(b"%PDF-1.4\n")
    (job / "Subject Information" / "PRC_The subject.pdf").write_bytes(b"%PDF-1.4\n")
    body = api.get("/api/jobs/A job/improvements/sources").json()
    names = [c["name"] for c in body["cards"]]
    assert names == ["PRC_The subject.pdf"], names


def test_the_section_transcript_outranks_the_neighbourhood_one(client):
    api, job = client
    (job / "Transcripts" / "Transcript Neighborhood.docx").write_bytes(b"PK\x03\x04")
    (job / "Transcripts" / "TRANSCRIPT Improvements.docx").write_bytes(b"PK\x03\x04")
    body = api.get("/api/jobs/A job/improvements/sources").json()
    assert "Improvements" in body["transcripts"][0]["name"]


def test_reading_needs_a_key_and_says_so_plainly(client):
    api, job = client
    (job / "Subject Information" / "PRC_x.pdf").write_bytes(b"%PDF-1.4\n")
    (job / "Transcripts" / "TRANSCRIPT Improvements.docx").write_bytes(b"PK\x03\x04")
    r = api.post("/api/jobs/A job/improvements/read", json={"confirmed": True})
    assert r.status_code == 400
    assert "Settings" in r.json()["detail"]


def test_writing_a_paragraph_needs_a_key(client):
    api, _ = client
    r = api.post("/api/jobs/A job/improvements/paragraph",
                 json={"block": "GENERAL", "facts": ["A fact."], "notes": ""})
    assert r.status_code == 400


def test_a_job_missing_one_source_is_refused(client):
    api, job = client
    (job / "Subject Information" / "PRC_x.pdf").write_bytes(b"%PDF-1.4\n")
    r = api.post("/api/jobs/A job/improvements/read", json={"confirmed": True})
    assert r.status_code == 400


def test_what_mark_ticked_is_saved_outside_his_job_folder(client, tmp_path):
    """Nothing the app records may reach one of his folders."""
    api, job = client
    before = sorted(p.name for p in job.rglob("*"))
    api.put("/api/jobs/A job/improvements",
            json={"blocks": [{"n": "GENERAL", "on": True}], "read": True})
    assert sorted(p.name for p in job.rglob("*")) == before
    assert (tmp_path / "store.json").is_file()
    back = api.get("/api/jobs/A job/improvements").json()
    assert back["read"] is True
    assert back["blocks"][0]["n"] == "GENERAL"


def test_a_job_never_saved_reads_as_empty_not_broken(client):
    api, _ = client
    body = api.get("/api/jobs/A job/improvements").json()
    assert body == {"blocks": [], "read": False}


def test_a_file_outside_the_job_cannot_be_read(client):
    api, job = client
    (job / "Subject Information" / "PRC_x.pdf").write_bytes(b"%PDF-1.4\n")
    (job / "Transcripts" / "TRANSCRIPT Improvements.docx").write_bytes(b"PK\x03\x04")
    r = api.post("/api/jobs/A job/improvements/read",
                 json={"card": "../../../etc/hosts", "transcript": "x", "confirmed": True})
    assert r.status_code == 400

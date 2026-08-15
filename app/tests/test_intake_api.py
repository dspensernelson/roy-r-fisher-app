import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
from main import create_app  # noqa: E402
import brief  # noqa: E402
import jobs  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / "jobs"
    home.mkdir()
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    return TestClient(create_app()), home


def payload(**over):
    body = {
        "name": "MASON CITY_4151 4th St SW - 2026 Tax",
        "street": "4151 4th St SW", "city": "Mason City", "state": "Iowa",
        "property_type": "retail", "engagement": "Tax appeal",
        "client": "Mason City Board of Review", "intended_use": "property tax appeal",
        "effective_date": "January 1, 2026", "due_date": "June 15, 2026",
        "file_number": "26-041",
    }
    body.update(over)
    return body


def test_propose_name_returns_the_house_style(client):
    c, _ = client
    r = c.post("/api/intake/propose-name", json={
        "city": "Mason City", "street": "4151 4th St SW",
        "engagement": "Tax appeal", "year": 2026})
    assert r.json()["name"] == "MASON CITY_4151 4th St SW - 2026 Tax"


def test_creating_a_job_makes_marks_own_eight_folders(client):
    c, home = client
    assert c.post("/api/intake", json=payload()).status_code == 200
    job = home / "MASON CITY_4151 4th St SW - 2026 Tax"
    for folder in jobs.MARK_FOLDERS:
        assert (job / folder).is_dir(), f"{folder} should exist in a new job"
    assert not (job / "Output").exists()      # appears only when something needs it


def test_creating_a_job_writes_the_brief(client):
    c, home = client
    c.post("/api/intake", json=payload())
    fields = brief.read_brief(home / "MASON CITY_4151 4th St SW - 2026 Tax")["fields"]
    assert fields["Property address"] == "4151 4th St SW, Mason City, Iowa"
    assert fields["Property type"] == "retail"
    assert fields["Engagement type"] == "Tax appeal"
    assert fields["Report due date"] == "June 15, 2026"
    assert fields["Office file number"] == "26-041"


def test_the_fields_that_block_creation_are_the_three_that_decide_the_job(client):
    c, _ = client
    for missing in ["street", "city", "property_type", "engagement"]:
        r = c.post("/api/intake", json=payload(**{missing: ""}))
        assert r.status_code == 400, f"an empty {missing} should be refused"


def test_everything_else_may_be_left_blank(client):
    c, home = client
    r = c.post("/api/intake", json=payload(
        client="", intended_use="", effective_date="", due_date="", file_number=""))
    assert r.status_code == 200, r.text
    fields = brief.read_brief(home / "MASON CITY_4151 4th St SW - 2026 Tax")["fields"]
    assert fields["Property address"] == "4151 4th St SW, Mason City, Iowa"
    assert fields["Report due date"] == ""


def test_a_duplicate_is_an_error_not_a_merge(client):
    c, _ = client
    assert c.post("/api/intake", json=payload()).status_code == 200
    assert c.post("/api/intake", json=payload()).status_code == 409


def test_a_name_that_escapes_the_jobs_home_is_refused(client):
    c, home = client
    assert c.post("/api/intake", json=payload(name="../evil")).status_code == 400
    assert c.post("/api/intake", json=payload(name="..\\evil")).status_code == 400
    assert not (home.parent / "evil").exists()


def test_an_engagement_the_matrix_does_not_know_is_refused(client):
    c, _ = client
    r = c.post("/api/intake", json=payload(engagement="Divorce appraisal"))
    assert r.status_code == 400


def test_a_fee_can_never_reach_the_brief(client, home_text=None):
    c, home = client
    c.post("/api/intake", json=payload(client="City of Mason City, fee $4,500 per letter"))
    text = (home / "MASON CITY_4151 4th St SW - 2026 Tax" / "job-brief.md").read_text()
    assert "$4,500" not in text
    assert "engagement letter" in text.lower()

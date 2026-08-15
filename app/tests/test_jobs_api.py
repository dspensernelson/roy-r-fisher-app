import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
from main import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / "jobs"
    home.mkdir()
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    return TestClient(create_app()), home


def test_a_hand_made_folder_starts_not_active(client):
    """The Jobs screen is his working list, not everything on disk. A folder
    that appears in Explorer is offered under Manage active jobs and shows up
    on the Jobs screen only once he says he is working on it."""
    c, home = client
    assert c.get("/api/jobs").json() == []
    (home / "DAVENPORT_1 Test St").mkdir()          # made "by hand in Explorer"
    assert c.get("/api/jobs").json() == []

    listed = c.get("/api/workspace/folders").json()
    assert listed["folders"] == ["DAVENPORT_1 Test St"]
    assert listed["active"] == []

    c.put("/api/workspace/folders", json={"active": ["DAVENPORT_1 Test St"]})
    assert [j["name"] for j in c.get("/api/jobs").json()] == ["DAVENPORT_1 Test St"]


def test_create_job_makes_marks_own_eight_folders(client):
    """No template is copied any more. The app makes his folders itself, so a
    job it creates is indistinguishable from one he made in Explorer, and it
    does not depend on a corpus folder that will not exist on his machine."""
    import jobs as jobs_mod
    c, home = client
    r = c.post("/api/jobs", json={"name": "MASON CITY_New Job"})
    assert r.status_code == 200
    job = home / "MASON CITY_New Job"
    for folder in jobs_mod.MARK_FOLDERS:
        assert (job / folder).is_dir(), f"{folder} should exist in a new job"
    assert not (job / "Output").exists()      # appears only when something needs it


def test_create_rejects_traversal_and_duplicates(client):
    c, home = client
    assert c.post("/api/jobs", json={"name": "../evil"}).status_code == 400
    c.post("/api/jobs", json={"name": "Dup"})
    assert c.post("/api/jobs", json={"name": "Dup"}).status_code == 409


def test_create_rejects_absolute_and_backslash_traversal(client):
    c, home = client
    assert c.post("/api/jobs", json={"name": "/etc/evil"}).status_code == 400
    assert c.post("/api/jobs", json={"name": "..\\evil"}).status_code == 400
    assert c.post("/api/jobs", json={"name": "sub\\..\\..\\evil"}).status_code == 400
    # confirm nothing escaped the jobs home
    assert not (home.parent / "evil").exists()


def test_detail_rejects_traversal_lookup(client):
    c, home = client
    assert c.get("/api/jobs/..%2F..%2Fevil").status_code in (400, 404)
    assert c.get("/api/jobs/..\\evil").status_code in (400, 404)


def test_detail_reads_job_brief_context(client):
    c, home = client
    job = home / "DAVENPORT_5348 Elmore"
    (job / "Photos").mkdir(parents=True)
    (job / "job-brief.md").write_text(
        "# Job Brief - DAVENPORT_5348 Elmore\n"
        "\n"
        "## Assignment\n"
        "\n"
        "| Field | Value |\n"
        "|---|---|\n"
        "| Property address | 5348 Elmore Circle, Davenport, Iowa |\n"
        "| Property type | industrial (flex/warehouse) |\n"
        "| Engagement type | tax appeal |\n"
    )
    detail = c.get("/api/jobs/DAVENPORT_5348 Elmore").json()
    assert "5348 Elmore Circle" in detail["context"]
    assert "industrial (flex/warehouse)" in detail["context"]
    assert detail["photo_count"] == 0


def test_detail_carries_the_chosen_sections_and_the_engagement(client):
    c, home = client
    job = home / "SECTIONED"
    (job / "Photos").mkdir(parents=True)
    (job / "job-brief.md").write_text(
        "## Assignment\n\n| Field | Value |\n|---|---|\n"
        "| Property address | 1 Main St |\n"
        "| Engagement type | Tax appeal |\n\n"
        "## Sections in this report\n\n| Section | Donor |\n|---|---|\n"
        "| Subject Photographs | Utica |\n| Site Analysis | Utica |\n"
    )
    detail = c.get("/api/jobs/SECTIONED").json()
    assert detail["sections"] == ["Subject Photographs", "Site Analysis"]
    assert detail["engagement"] == "Tax appeal"


def test_detail_of_a_job_with_no_brief_has_no_sections(client):
    c, home = client
    (home / "BARE" / "Photos").mkdir(parents=True)
    detail = c.get("/api/jobs/BARE").json()
    assert detail["sections"] == []
    assert detail["engagement"] == ""


def test_detail_context_handles_partial_and_missing_brief(client):
    c, home = client

    only_address = home / "ONLY_ADDRESS"
    (only_address / "Photos").mkdir(parents=True)
    (only_address / "job-brief.md").write_text(
        "## Assignment\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        "| Property address | 100 Main St, Anywhere, IA |\n"
    )
    detail = c.get("/api/jobs/ONLY_ADDRESS").json()
    assert detail["context"] == "100 Main St, Anywhere, IA"

    no_brief = home / "NO_BRIEF"
    (no_brief / "Photos").mkdir(parents=True)
    detail = c.get("/api/jobs/NO_BRIEF").json()
    assert detail["context"] == ""

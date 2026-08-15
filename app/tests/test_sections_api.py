import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
from main import create_app  # noqa: E402
import brief  # noqa: E402
import sections as sections_mod  # noqa: E402

MATRIX_PRESENT = pytest.mark.skipif(
    not sections_mod.MATRIX.is_file(), reason="shop engagement matrix not present"
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / "jobs"
    home.mkdir()
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    job = home / "JOB1"
    (job / "Photos").mkdir(parents=True)
    brief.write_brief(job, {"Property address": "1 Main St, Davenport, Iowa",
                            "Property type": "retail",
                            "Engagement type": "Tax appeal"}, [])
    return TestClient(create_app()), job


@MATRIX_PRESENT
def test_before_choosing_the_proposal_is_shown(client):
    c, _ = client
    body = c.get("/api/jobs/JOB1/sections").json()
    assert body["engagement"] == "Tax appeal"
    assert body["chosen"] is False
    assert body["thin_evidence"] is False
    on = [s["name"] for s in body["sections"] if s["chosen"]]
    assert "Salient Facts Summary" in on
    assert "Regional and City Data" not in on      # qualified, offered unchecked


@MATRIX_PRESENT
def test_saving_choices_writes_them_to_the_brief_and_reads_back(client):
    c, job = client
    r = c.put("/api/jobs/JOB1/sections",
              json={"sections": ["Title Page", "Subject Photographs", "Certification"]})
    assert r.status_code == 200
    assert brief.read_brief(job)["sections"] == ["Title Page", "Subject Photographs", "Certification"]
    body = c.get("/api/jobs/JOB1/sections").json()
    assert body["chosen"] is True
    assert [s["name"] for s in body["sections"] if s["chosen"]] == \
        ["Title Page", "Subject Photographs", "Certification"]


@MATRIX_PRESENT
def test_saving_choices_never_disturbs_the_assignment_fields(client):
    c, job = client
    c.put("/api/jobs/JOB1/sections", json={"sections": ["Title Page"]})
    fields = brief.read_brief(job)["fields"]
    assert fields["Property address"] == "1 Main St, Davenport, Iowa"
    assert fields["Engagement type"] == "Tax appeal"


@MATRIX_PRESENT
def test_a_section_mark_added_by_hand_survives(client):
    c, _ = client
    c.put("/api/jobs/JOB1/sections", json={"sections": ["Title Page", "Damages"]})
    body = c.get("/api/jobs/JOB1/sections").json()
    names = [s["name"] for s in body["sections"]]
    assert "Damages" in names           # not in the matrix, still shown and kept
    assert [s for s in body["sections"] if s["name"] == "Damages"][0]["chosen"] is True


def test_sections_for_an_unknown_job_is_a_404(client):
    c, _ = client
    assert c.get("/api/jobs/NOPE/sections").status_code == 404
    assert c.put("/api/jobs/NOPE/sections", json={"sections": []}).status_code == 404


def test_a_job_with_no_engagement_type_says_so_instead_of_guessing(client, tmp_path):
    c, _ = client
    (tmp_path / "jobs" / "BARE" / "Photos").mkdir(parents=True)
    body = c.get("/api/jobs/BARE/sections").json()
    assert body["engagement"] == ""
    assert body["sections"] == []

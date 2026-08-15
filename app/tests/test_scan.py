import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from main import create_app  # noqa: E402
import scan  # noqa: E402
import readiness_scan  # noqa: E402
import jobs  # noqa: E402


def make_job(home: Path, name: str = "JOB1") -> Path:
    job = home / name
    for folder in jobs.MARK_FOLDERS:
        (job / folder).mkdir(parents=True)
    return job


@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / "jobs"
    home.mkdir()
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    return TestClient(create_app()), make_job(home)


def test_scan_job_finds_a_planted_input_and_reports_a_missing_one(tmp_path):
    job = make_job(tmp_path)
    (job / "Subject Information" / "Signed Engagement Letter.pdf").write_bytes(b"x")
    result = readiness_scan.scan_job(job)
    intake = result["sections"]["Intake docs"]
    letter = [c for c in intake if "engagement" in c["note"]][0]
    deed = [c for c in intake if c["note"] == "deed"][0]
    assert letter["hits"] == ["Subject Information/Signed Engagement Letter.pdf"]
    assert deed["hits"] == []


def test_scan_job_reports_workbook_and_brief(tmp_path):
    job = make_job(tmp_path)
    assert readiness_scan.scan_job(job)["workbook"] is None
    assert readiness_scan.scan_job(job)["brief"] is False
    (job / "Valuation.xlsm").write_bytes(b"x")
    (job / "job-brief.md").write_text("# Job Brief\n")
    result = readiness_scan.scan_job(job)
    assert result["workbook"] == "Valuation.xlsm"
    assert result["brief"] is True


def test_cli_still_prints_its_report(tmp_path, capsys):
    job = make_job(tmp_path)
    readiness_scan.main(str(job))
    printed = capsys.readouterr().out
    assert "READINESS SCAN" in printed
    assert "[Intake docs]" in printed
    assert "[Photos]" in printed
    assert "[Comps]" in printed
    assert "[Job xlsm]" in printed
    assert "[job-brief.md]" in printed


def test_folder_rows_cover_every_folder_in_order(tmp_path):
    job = make_job(tmp_path)
    rows = scan.folder_rows(job)
    assert [r["folder"] for r in rows] == jobs.MARK_FOLDERS


def test_folder_rows_split_here_from_needed(tmp_path):
    job = make_job(tmp_path)
    (job / "Maps" / "Plat Map.pdf").write_bytes(b"x")
    rows = {r["folder"]: r for r in scan.folder_rows(job)}
    assert "plat map" in rows["Maps"]["here"]
    assert "flood map" in rows["Maps"]["needs"]
    assert rows["Maps"]["status"] == "waiting"
    assert rows["Maps"]["count"] == 1


def test_an_empty_photos_folder_says_it_needs_photos(tmp_path):
    """The scan table carries no filename patterns for Photos or Comps, so
    without this those two rows would report "nothing missing" while sitting
    empty. They are the two folders the appraiser fills first, so a vacuous all-clear
    there would be the most misleading line on the screen."""
    job = make_job(tmp_path)
    rows = {r["folder"]: r for r in scan.folder_rows(job)}
    assert rows["Photos"]["needs"] == ["photos"]
    assert rows["Photos"]["status"] == "waiting"
    assert rows["Comps"]["needs"] == ["comparable sales"]
    assert rows["Comps"]["status"] == "waiting"


def test_folder_rows_counts_photos_and_clears_the_row(tmp_path):
    job = make_job(tmp_path)
    for i in range(3):
        (job / "Photos" / f"IMG_{i}.jpg").write_bytes(b"x")
    rows = {r["folder"]: r for r in scan.folder_rows(job)}
    assert rows["Photos"]["count"] == 3
    assert rows["Photos"]["needs"] == []
    assert rows["Photos"]["here"] == ["photos"]
    assert rows["Photos"]["status"] == "ready"


def test_comps_row_clears_once_comp_documents_arrive(tmp_path):
    job = make_job(tmp_path)
    (job / "Comps" / "Comp 1.pdf").write_bytes(b"x")
    rows = {r["folder"]: r for r in scan.folder_rows(job)}
    assert rows["Comps"]["needs"] == []
    assert rows["Comps"]["here"] == ["comparable sales"]


def test_scan_endpoint_returns_folder_rows(client):
    c, job = client
    (job / "Subject Information" / "Deed.pdf").write_bytes(b"x")
    body = c.get("/api/jobs/JOB1/scan").json()
    subject = [f for f in body["folders"] if f["folder"] == "Subject Information"][0]
    assert "deed" in subject["here"]
    assert c.get("/api/jobs/NOPE/scan").status_code == 404

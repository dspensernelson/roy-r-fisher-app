import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from main import create_app  # noqa: E402
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

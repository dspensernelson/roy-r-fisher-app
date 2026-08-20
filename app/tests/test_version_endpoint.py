"""Which version is answering, and why one endpoint does three jobs.

The launcher probes this to tell our app from anything else on a port, the
screens show it so Mark knows which folder he opened, and the last-good record
is checked against it. It replaced a probe of /api/demo, which could never have
worked in the package Mark receives because the demo routes are excluded from
it.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import packaging  # noqa: E402
from main import create_app  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def client():
    return TestClient(create_app())


def test_it_answers_with_the_version_file(client):
    response = client.get("/api/version")
    assert response.status_code == 200
    assert response.json() == {"version": packaging.version_of(REPO)}


def test_the_version_file_exists_and_is_a_plain_string():
    found = packaging.version_of(REPO)
    assert found
    assert "\n" not in found
    assert found == (REPO / "VERSION").read_text(encoding="utf-8").strip()


def test_it_needs_no_key_no_jobs_folder_and_no_setup(client, monkeypatch):
    """The launcher probes this before anything is configured, so it must
    answer on a machine where nothing has been set up yet."""
    monkeypatch.delenv("RRF_JOBS_HOME", raising=False)
    assert client.get("/api/version").status_code == 200


def test_it_leaks_nothing_else(client):
    body = client.get("/api/version").json()
    assert set(body) == {"version"}


def test_a_missing_version_file_is_empty_never_a_guess(tmp_path):
    assert packaging.version_of(tmp_path) == ""


def test_the_demo_probe_is_not_what_the_launcher_uses():
    """The defect this endpoint exists to fix: /api/demo is excluded from the
    package, so a launcher probing it would work on the Mac and fail on Mark's
    machine, which is the worst shape a defect can have."""
    launcher = (REPO / "app" / "run_app.py").read_text(encoding="utf-8")
    startup_source = (REPO / "app" / "server" / "startup.py").read_text(encoding="utf-8")
    assert "/api/demo" not in launcher
    assert "/api/demo" not in startup_source
    assert "/api/version" in startup_source

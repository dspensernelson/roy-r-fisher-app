"""Marking every caption reviewed in one go.

Wanted by Spenser on 2026-09-02, restated on 2026-09-03 as something that has
to exist, and asked for again on 2026-09-07 because Colleen was clicking a
tick per photograph on a network drive.

**It sits behind a warning, and that is his rule, in his own words: it is very
important that humans review everything AI does.** The warning belongs on the
screen. What this file holds is the promise the screen depends on: one request
instead of fifty, and nothing ticked that a person could not have ticked
himself.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import jobs  # noqa: E402
from main import create_app  # noqa: E402

MANIFEST = {
    "job": "A job",
    "caption_style": "view",
    "photos": [{"file": "a.jpg", "caption": "View east"},
               {"file": "b.jpg", "caption": "The middle one"},
               {"file": "c.jpg", "caption": "", },
               {"file": "d.jpg", "caption": "Out of the report", "cut": True}],
}


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path / "jobs"))
    where = tmp_path / "jobs" / "A job" / "Photos"
    where.mkdir(parents=True)
    for entry in MANIFEST["photos"]:
        (where / entry["file"]).write_bytes(b"pretend jpeg " + entry["file"].encode())
    (where / "photo-manifest.json").write_text(json.dumps(MANIFEST, indent=2))
    return tmp_path / "jobs"


@pytest.fixture
def client(home):
    return TestClient(create_app())


@pytest.fixture
def listings(monkeypatch):
    seen = []
    real = jobs.photo_files
    monkeypatch.setattr(jobs, "photo_files", lambda job: (seen.append(1), real(job))[1])
    return seen


def on_disk(home) -> dict:
    return {e["file"]: e for e in json.loads(
        (home / "A job" / "Photos" / "photo-manifest.json").read_text())["photos"]}


def test_every_caption_that_is_written_gets_its_tick(client, home):
    r = client.post("/api/jobs/A job/review-all")
    assert r.status_code == 200
    kept = on_disk(home)
    assert kept["a.jpg"]["reviewed"] is True
    assert kept["b.jpg"]["reviewed"] is True


def test_a_photograph_with_no_caption_is_left_alone(client, home):
    """The same rule one tick follows. There is nothing to have read."""
    assert client.post("/api/jobs/A job/review-all").status_code == 200
    assert "reviewed" not in on_disk(home)["c.jpg"]


def test_a_photograph_taken_out_is_left_alone(client, home):
    """It is not in the report, so it needs no caption and no reading."""
    assert client.post("/api/jobs/A job/review-all").status_code == 200
    assert "reviewed" not in on_disk(home)["d.jpg"]


def test_it_says_how_many_it_ticked(client):
    """So the screen can say what happened rather than going quiet."""
    r = client.post("/api/jobs/A job/review-all")
    assert r.json()["marked"] == 2


def test_the_build_is_still_held_while_a_caption_is_missing(client):
    """Marking all is not a way past the gate. One photograph here has no
    caption, so the job is not ready and must not say it is."""
    r = client.post("/api/jobs/A job/review-all")
    assert r.json()["review"]["all_reviewed"] is False


def test_it_never_lists_the_photo_folder(client, listings):
    """One request instead of fifty is the point. Paying for a reconcile
    would hand back what the fifty cost."""
    assert client.post("/api/jobs/A job/review-all").status_code == 200
    assert listings == []


def test_a_job_this_app_does_not_have_is_refused(client):
    assert client.post("/api/jobs/No such job/review-all").status_code == 404

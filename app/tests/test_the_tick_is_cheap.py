"""Ticking a caption must not re-read the whole photo folder.

Colleen keeps her photographs on a mapped network drive. Reported by Spenser
on 2026-09-07: there is too much of a delay in the reviewed click. Measured
here on 2026-09-07, on the 124-photograph Cedar Rapids job, on a local disk:

    listing the Photos folder          3.6 ms
    the whole reconcile a tick does    9.5 ms
    reading the list off disk only     0.0 ms
    writing it back, with a backup     0.8 ms

Every one of those file operations is a round trip on her drive rather than a
local read, which is why 9.5 ms here is a wait there. A tick changes one key
and needs none of it: the folder cannot have changed because of the click.

What the tick still must do is answer with the photographs that are in the
report, not every photograph on disk, so the screen does not gain tiles it
was never shown. That narrowing reads the job's own notes and never the
folder, which is what makes the cheap path safe.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import jobs  # noqa: E402
import photos as photos_routes  # noqa: E402
from main import create_app  # noqa: E402

MANIFEST = {
    "job": "A job",
    "caption_style": "view",
    "photos": [{"file": "a.jpg", "caption": "View east"},
               {"file": "b.jpg", "caption": "The middle one"},
               {"file": "c.jpg", "caption": "Rear loading area"}],
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
    """Every time anything lists the job's Photos folder, it lands here."""
    seen = []
    real_files, real_names = jobs.photo_files, jobs.photo_names

    def files(job):
        seen.append("photo_files")
        return real_files(job)

    def names(job):
        seen.append("photo_names")
        return real_names(job)

    monkeypatch.setattr(jobs, "photo_files", files)
    monkeypatch.setattr(jobs, "photo_names", names)
    return seen


def on_disk(home) -> dict:
    return json.loads((home / "A job" / "Photos" / "photo-manifest.json").read_text())


@pytest.fixture
def resolved(monkeypatch):
    """Every path the app resolves against the Photos folder lands here.

    Resolving is a filesystem round trip. Doing it for all 124 photographs to
    write one boolean is the rest of Colleen's wait.
    """
    seen = []
    real = photos_routes._resolve_confined

    def counted(path, base):
        seen.append(path)
        return real(path, base)

    monkeypatch.setattr(photos_routes, "_resolve_confined", counted)
    return seen


def test_a_tick_checks_the_photograph_it_touches_and_not_the_rest(client, resolved):
    """The confinement check is what stops a manifest naming a file outside
    the Photos folder. A tick changes no path, so the one it touches is the
    one worth checking, and the build checks every entry again before it
    writes a document."""
    r = client.post("/api/jobs/A job/photos/a.jpg/reviewed")
    assert r.status_code == 200
    assert len(resolved) <= 1, "a tick resolved every photograph in the job"


def test_a_tick_still_refuses_a_photograph_that_escapes_the_folder(client, home):
    """Cheaper must not mean unguarded."""
    where = home / "A job" / "Photos" / "photo-manifest.json"
    bad = json.loads(where.read_text())
    bad["photos"][0]["folder"] = "../.."
    where.write_text(json.dumps(bad))
    r = client.post("/api/jobs/A job/photos/a.jpg/reviewed")
    assert r.status_code == 400


def test_ticking_a_caption_never_lists_the_photo_folder(client, home, listings):
    r = client.post("/api/jobs/A job/photos/a.jpg/reviewed")
    assert r.status_code == 200
    assert listings == [], "a tick paid for a folder listing it does not need"


def test_unticking_never_lists_it_either(client, home, listings):
    client.post("/api/jobs/A job/photos/a.jpg/reviewed")
    listings.clear()
    r = client.post("/api/jobs/A job/photos/a.jpg/unreviewed")
    assert r.status_code == 200
    assert listings == []


def test_the_tick_still_lands_on_disk(client, home):
    client.post("/api/jobs/A job/photos/a.jpg/reviewed")
    kept = {e["file"]: e.get("reviewed") for e in on_disk(home)["photos"]}
    assert kept == {"a.jpg": True, "b.jpg": None, "c.jpg": None}


def test_the_answer_still_carries_the_count_the_screen_shows(client):
    r = client.post("/api/jobs/A job/photos/a.jpg/reviewed")
    assert r.json()["review"]["text"] == "1 of 3 reviewed"


def test_the_answer_still_carries_the_photographs_in_the_report(client):
    r = client.post("/api/jobs/A job/photos/a.jpg/reviewed")
    assert [e["file"] for e in r.json()["photos"]] == ["a.jpg", "b.jpg", "c.jpg"]


def test_a_caption_must_still_be_written_before_it_can_be_ticked(client, home):
    (home / "A job" / "Photos" / "photo-manifest.json").write_text(json.dumps(
        {**MANIFEST, "photos": [{"file": "a.jpg", "caption": ""}]}, indent=2))
    r = client.post("/api/jobs/A job/photos/a.jpg/reviewed")
    assert r.status_code == 400


def test_a_photograph_this_job_does_not_have_is_still_refused(client):
    r = client.post("/api/jobs/A job/photos/nope.jpg/reviewed")
    assert r.status_code == 404

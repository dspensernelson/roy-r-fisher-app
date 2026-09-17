"""A tick means somebody read words. No words, no tick.

Found on 2026-09-17. `Clear captions` blanked every caption and left every
tick standing. The screen then offered `Build photo pages` in solid red for a
report in which every caption was empty, while the same bar said `0 written`.
Two parts of the app disagreeing about one job, and the one that won writes a
Word document into a folder Mark keeps.

The rule these tests hold: reviewed can never be more than written. A
photograph taken out of the report is outside both counts, so it can neither
add to them nor block a build.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import photos as photos_routes  # noqa: E402
from main import create_app  # noqa: E402

MANIFEST = {
    "job": "A job",
    "caption_style": "view",
    "photos": [
        {"file": "a.jpg", "caption": "View east", "reviewed": True},
        {"file": "b.jpg", "caption": "The middle one", "reviewed": True},
        {"file": "c.jpg", "caption": "The far corner", "reviewed": True},
        {"file": "d.jpg", "caption": "Out of the report", "reviewed": True,
         "cut": True},
    ],
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


def on_disk(home) -> dict:
    return {e["file"]: e for e in json.loads(
        (home / "A job" / "Photos" / "photo-manifest.json").read_text())["photos"]}


def rewrite(home, photos) -> None:
    """Put a list of photographs on disk by hand, the way a person editing
    photo-manifest.json in Notepad would. The file is hand-editable by
    design, so this is a real state and not a synthetic one."""
    path = home / "A job" / "Photos" / "photo-manifest.json"
    path.write_text(json.dumps({**MANIFEST, "photos": photos}, indent=2))


# --- clearing captions ------------------------------------------------------

def test_clearing_captions_takes_every_tick_off(client, home):
    assert client.post("/api/jobs/A job/captions/clear").status_code == 200
    for name, entry in on_disk(home).items():
        assert not entry.get("reviewed"), name
        assert entry["caption"] == ""


def test_the_answer_it_sends_back_carries_no_tick(client):
    answer = client.post("/api/jobs/A job/captions/clear").json()
    assert answer["cleared"] == 4
    assert [p for p in answer["photos"] if p.get("reviewed")] == []


def test_after_clearing_the_two_counts_agree(client, home):
    client.post("/api/jobs/A job/captions/clear")
    progress = photos_routes.review_progress(
        photos_routes.load_manifest(home / "A job"))
    assert progress["reviewed"] == 0
    assert progress["included"] == 3
    assert progress["text"] == "0 of 3 reviewed"
    assert progress["all_reviewed"] is False


def test_build_is_not_offered_after_clearing(client):
    client.post("/api/jobs/A job/captions/clear")
    r = client.post("/api/jobs/A job/build")
    assert r.status_code == 400
    assert "reviewed" in r.json()["detail"]


# --- a photograph taken out of the report -----------------------------------

def test_a_photograph_taken_out_is_outside_both_counts(client, home):
    """It needs no caption and no reading, so a blank one cannot hold a
    build back and a ticked one cannot pad the count."""
    rewrite(home, [
        {"file": "a.jpg", "caption": "View east", "reviewed": True},
        {"file": "b.jpg", "caption": "The middle one", "reviewed": True},
        {"file": "c.jpg", "caption": "The far corner", "reviewed": True},
        {"file": "d.jpg", "caption": "", "cut": True},
    ])
    progress = photos_routes.review_progress(
        photos_routes.load_manifest(home / "A job"))
    assert progress["included"] == 3
    assert progress["reviewed"] == 3
    assert progress["all_reviewed"] is True


def test_clearing_does_not_leave_a_tick_on_a_photograph_taken_out(client, home):
    client.post("/api/jobs/A job/captions/clear")
    assert not on_disk(home)["d.jpg"].get("reviewed")


# --- the hand-edited file ---------------------------------------------------

def test_a_tick_written_by_hand_without_words_does_not_count(client, home):
    """The manifest is hand-editable, so this is the door the build gate
    exists to close."""
    rewrite(home, [
        {"file": "a.jpg", "caption": "", "reviewed": True},
        {"file": "b.jpg", "caption": "", "reviewed": True},
        {"file": "c.jpg", "caption": "", "reviewed": True},
        {"file": "d.jpg", "caption": "", "reviewed": True, "cut": True},
    ])
    progress = photos_routes.review_progress(
        photos_routes.load_manifest(home / "A job"))
    assert progress["reviewed"] == 0
    assert progress["all_reviewed"] is False
    r = client.post("/api/jobs/A job/build")
    assert r.status_code == 400
    assert "reviewed" in r.json()["detail"]


def test_a_tick_without_words_never_reaches_the_screen(client, home):
    """The screen draws its ticks and counts its pills from what it is sent.
    If a tick that means nothing reaches it, the screen goes on offering a
    build the server would refuse."""
    rewrite(home, [
        {"file": "a.jpg", "caption": "", "reviewed": True},
        {"file": "b.jpg", "caption": "The middle one", "reviewed": True},
        {"file": "c.jpg", "caption": "The far corner", "reviewed": True},
        {"file": "d.jpg", "caption": "Out of the report", "reviewed": True,
         "cut": True},
    ])
    sent = client.get("/api/jobs/A job/manifest").json()["photos"]
    ticked = {p["file"] for p in sent if p.get("reviewed")}
    assert ticked == {"b.jpg", "c.jpg", "d.jpg"}


# --- nothing else moves -----------------------------------------------------

def test_a_tick_with_words_is_left_alone(client, home):
    """The fix must not start taking ticks off work that was really read."""
    client.put("/api/jobs/A job/facts",
               json={"city": "Davenport", "address": "1 Test Street"})
    sent = client.get("/api/jobs/A job/manifest").json()["photos"]
    assert ({p["file"] for p in sent if p.get("reviewed")}
            == {"a.jpg", "b.jpg", "c.jpg", "d.jpg"})
    progress = photos_routes.review_progress(
        photos_routes.load_manifest(home / "A job"))
    assert progress["all_reviewed"] is True
    assert progress["text"] == "3 of 3 reviewed"

"""Who wrote each caption: the AI, or a person.

Spenser, 2026-09-18: **a caption he types himself counts as reviewed.** He
wrote it, so he has read it. His standing rule is that a person reviews
everything the AI does, and a typed caption was never the AI's.

So the app records, per photograph, who wrote the words on it, and sets that
at every place words are written. A typed caption is ticked when it is saved,
which is when he leaves the box and never on a keystroke. An AI caption waits
for his tick exactly as before.

Old manifests carry no author. Every caption in them is read as the AI's, so
nothing is ticked that was not ticked before.

Real folders and real manifest files on disk. The model is stood in for.
"""
import io
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import captions  # noqa: E402
import jobs as jobs_module  # noqa: E402
import photos as photos_routes  # noqa: E402
from main import create_app  # noqa: E402

JOB = "DAVENPORT_2840 Brady Street - 2026 Tax"
USED = {"input": 1000, "output": 200, "cache_write": 0, "cache_read": 0}
AUTHOR = photos_routes.AUTHOR

# A manifest written before authors existed: no key on any of them.
OLD = [
    {"file": "a.jpg", "caption": "View east from Brady Street", "reviewed": True},
    {"file": "b.jpg", "caption": "Rear loading area"},
    {"file": "c.jpg", "caption": ""},
    {"file": "d.jpg", "caption": ""},
]


def jpg_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (30, 20), (10, 20, 30)).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path / "jobs"))
    monkeypatch.setenv("RRF_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("RRF_USAGE_FILE", str(tmp_path / "usage.json"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-not-a-real-key")
    job = tmp_path / "jobs" / JOB
    for folder in jobs_module.MARK_FOLDERS:
        (job / folder).mkdir(parents=True)
    for entry in OLD:
        (job / "Photos" / entry["file"]).write_bytes(jpg_bytes())
    (job / "Photos" / "photo-manifest.json").write_text(json.dumps(
        {"job": JOB, "context": "2840 Brady Street, Davenport",
         "report_year": 2026, "caption_style": "view",
         "photos": [dict(e) for e in OLD]}, indent=2))
    return tmp_path / "jobs"


@pytest.fixture
def client(home):
    return TestClient(create_app(), raise_server_exceptions=False)


def disk(home) -> dict:
    m = json.loads((home / JOB / "Photos" / "photo-manifest.json").read_text())
    return {e["file"]: e for e in m["photos"]}


def served(client) -> dict:
    return {e["file"]: e for e in client.get("/api/jobs/%s/manifest" % JOB).json()["photos"]}


def type_caption(client, file, words):
    """What the screen does when he leaves a caption box: send the job back
    with that one caption changed."""
    m = client.get("/api/jobs/%s/manifest" % JOB).json()
    for e in m["photos"]:
        if e["file"] == file:
            e["caption"] = words
    return client.put("/api/jobs/%s/manifest" % JOB, json=m)


def stand_in(monkeypatch, words="View of a newly written thing"):
    def fake(context, paths, style=None):
        return ({p.name: words for p in paths}, dict(USED))
    monkeypatch.setattr(captions, "draft_captions", fake)


# --- old manifests --------------------------------------------------------
def test_an_old_caption_is_read_as_the_ais(client):
    got = served(client)
    assert got["a.jpg"][AUTHOR] == "ai"
    assert got["b.jpg"][AUTHOR] == "ai"


def test_an_old_caption_gains_no_tick(client):
    """Nothing that was not ticked before is ticked now."""
    got = served(client)
    assert got["a.jpg"].get("reviewed") is True
    assert not got["b.jpg"].get("reviewed")


def test_a_blank_caption_has_no_author(client):
    assert AUTHOR not in served(client)["c.jpg"]


# --- typed by him -----------------------------------------------------------
def test_a_typed_caption_is_his_and_is_ticked(client, home):
    assert type_caption(client, "c.jpg", "Front entry, looking north").status_code == 200
    kept = disk(home)["c.jpg"]
    assert kept[AUTHOR] == "person"
    assert kept["reviewed"] is True


def test_editing_an_ai_caption_makes_it_his(client, home):
    type_caption(client, "b.jpg", "Rear loading area and dock doors")
    kept = disk(home)["b.jpg"]
    assert kept[AUTHOR] == "person"
    assert kept["reviewed"] is True


def test_saving_the_job_without_changing_the_words_changes_no_author(client, home):
    """A reorder or a per-page change sends every caption back unchanged. None
    of them becomes his, and none gains a tick."""
    m = client.get("/api/jobs/%s/manifest" % JOB).json()
    m["photos"].reverse()
    client.put("/api/jobs/%s/manifest" % JOB, json=m)
    kept = disk(home)
    assert kept["b.jpg"][AUTHOR] == "ai"
    assert not kept["b.jpg"].get("reviewed")


def test_the_screen_cannot_claim_a_caption_it_did_not_change(client, home):
    """Who wrote the words is the server's fact. A manifest sent back saying
    an unchanged AI caption is his is not believed."""
    m = client.get("/api/jobs/%s/manifest" % JOB).json()
    for e in m["photos"]:
        if e["file"] == "b.jpg":
            e[AUTHOR] = "person"
    client.put("/api/jobs/%s/manifest" % JOB, json=m)
    assert disk(home)["b.jpg"][AUTHOR] == "ai"


def test_typing_a_caption_away_leaves_no_author_and_no_tick(client, home):
    type_caption(client, "a.jpg", "")
    kept = disk(home)["a.jpg"]
    assert AUTHOR not in kept
    assert not kept.get("reviewed")


def test_the_answer_carries_the_saved_caption_back(client):
    """The screen reads who wrote it and the tick from here, so it never works
    either out for itself."""
    body = type_caption(client, "c.jpg", "Front entry").json()
    entry = {e["file"]: e for e in body["manifest"]["photos"]}["c.jpg"]
    assert entry[AUTHOR] == "person" and entry["reviewed"] is True


# --- written by the AI ------------------------------------------------------
def test_a_run_writes_ai_captions_that_wait_for_his_tick(client, home, monkeypatch):
    stand_in(monkeypatch)
    assert client.post("/api/jobs/%s/captions" % JOB).status_code == 200
    kept = disk(home)
    for name in ("c.jpg", "d.jpg"):
        assert kept[name][AUTHOR] == "ai"
        assert not kept[name].get("reviewed")


def test_refresh_makes_a_typed_caption_the_ais_again(client, home, monkeypatch):
    type_caption(client, "c.jpg", "Front entry")
    stand_in(monkeypatch, words="View of the front entry")
    assert client.post("/api/jobs/%s/photos/c.jpg/caption" % JOB).status_code == 200
    kept = disk(home)["c.jpg"]
    assert kept[AUTHOR] == "ai"
    assert not kept.get("reviewed")


# --- clear and restore ------------------------------------------------------
def test_clear_takes_the_author_with_the_words(client, home):
    type_caption(client, "c.jpg", "Front entry")
    client.post("/api/jobs/%s/captions/clear" % JOB)
    for entry in disk(home).values():
        assert AUTHOR not in entry


def test_restore_puts_back_whoever_wrote_the_words(client, home):
    type_caption(client, "c.jpg", "Front entry")
    client.post("/api/jobs/%s/captions/clear" % JOB)
    client.post("/api/jobs/%s/captions/back" % JOB)
    kept = disk(home)
    assert kept["c.jpg"][AUTHOR] == "person"
    assert kept["b.jpg"][AUTHOR] == "ai"


def test_back_on_one_photograph_puts_back_its_author(client, home):
    type_caption(client, "c.jpg", "Front entry")
    client.post("/api/jobs/%s/captions/clear" % JOB)
    client.post("/api/jobs/%s/photos/c.jpg/caption/back" % JOB)
    assert disk(home)["c.jpg"][AUTHOR] == "person"


def test_restored_words_do_not_bring_a_tick(client, home):
    """Unchanged rule of 2026-09-17: the tick never comes back with the words,
    whoever wrote them."""
    type_caption(client, "c.jpg", "Front entry")
    client.post("/api/jobs/%s/captions/clear" % JOB)
    client.post("/api/jobs/%s/captions/back" % JOB)
    assert not disk(home)["c.jpg"].get("reviewed")


# --- the one rule, and the validator ----------------------------------------
def test_a_tick_still_needs_a_caption():
    assert not photos_routes.is_reviewed({"file": "x.jpg", "caption": "",
                                          "reviewed": True, AUTHOR: "person"})


def test_the_validator_refuses_an_author_it_does_not_know(client):
    m = client.get("/api/jobs/%s/manifest" % JOB).json()
    m["photos"][0][AUTHOR] = "somebody"
    r = client.put("/api/jobs/%s/manifest" % JOB, json=m)
    assert r.status_code == 400
    assert "wrote" in r.json()["detail"].lower()

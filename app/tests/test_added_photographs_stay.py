"""A photograph added with the button goes where the report can see it.

**One fault wearing four different hats.** Found by Colleen McDevitt Brown in
Mark's office on 2026-09-03, worked out by Spenser from the behaviour before
anybody read the code.

`store_upload` always wrote to the top of the `Photos` folder. `_report_set`
only keeps entries whose folder matches the one the office chose. So the app
put the photograph somewhere the report could not see, and every reconciliation
afterwards treated it as an outsider that did not belong.

What that looked like from her chair:

- She adds a photograph. It vanishes.                                     (B5)
- She adds it again, and again, so the folder fills with `(2)` and `(3)`
  copies of the same road sign.                                          (B2)
- She generates captions and the photographs she added are gone.         (B1)
- She takes one out and another goes with it.                            (B3)
- The build then refuses, naming a photograph it cannot find.            (B4)

The fix is one line of intent: **put it in the folder the report is pointed
at.** These tests are the four hats, so it cannot come back wearing any of
them.
"""
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import jobfacts  # noqa: E402
import photos  # noqa: E402
from main import create_app  # noqa: E402

JOB = "A JOB"
CHOSEN = "Original Photos_2377 US Highway 6"


def jpg(colour=(3, 3, 3)):
    buf = io.BytesIO()
    Image.new("RGB", (40, 30), colour).save(buf, format="JPEG")
    return buf.getvalue()


def upload(c, name, colour=(3, 3, 3)):
    return c.post("/api/jobs/%s/photos" % JOB,
                  files=[("files", (name, jpg(colour), "image/jpeg"))])


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A job shaped like Colleen's: photographs in a subfolder, and that
    subfolder chosen as the report."""
    home = tmp_path / "jobs"
    job = home / JOB
    (job / "Photos" / CHOSEN).mkdir(parents=True)
    for i in range(3):
        Image.new("RGB", (40, 30)).save(job / "Photos" / CHOSEN / ("IMG_%02d.jpeg" % i))
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    c = TestClient(create_app(), raise_server_exceptions=False)
    c.put("/api/jobs/%s/photo-group" % JOB, json={"folder": CHOSEN})
    return c, job


def names_on_screen(c):
    return [p["file"] for p in c.get("/api/jobs/%s/manifest" % JOB).json()["photos"]]


# --- B5: it appears at all --------------------------------------------------

def test_a_photograph_added_with_the_button_appears(client):
    c, job = client
    assert upload(c, "new one.jpeg").status_code == 200
    assert "new one.jpeg" in names_on_screen(c), "it was added and then hidden"


def test_it_lands_in_the_folder_the_report_uses(client):
    c, job = client
    upload(c, "new one.jpeg")
    assert (job / "Photos" / CHOSEN / "new one.jpeg").is_file()
    assert not (job / "Photos" / "new one.jpeg").exists(), \
        "it went to the top of Photos, where the report cannot see it"


def test_the_entry_records_the_folder_it_went_into(client):
    c, job = client
    upload(c, "new one.jpeg")
    entry = [p for p in c.get("/api/jobs/%s/manifest" % JOB).json()["photos"]
             if p["file"] == "new one.jpeg"][0]
    assert entry.get("folder") == CHOSEN


# --- B1: captions do not eat it ---------------------------------------------

def test_captions_do_not_remove_a_photograph_that_was_added(client, monkeypatch):
    """The one that stopped a real report. She added a photograph, ran
    captions, and it was gone."""
    c, job = client
    upload(c, "new one.jpeg")
    before = names_on_screen(c)
    assert "new one.jpeg" in before

    import captions as captions_module

    def fake(_context, batch, style=None):
        return {Path(p).name: "A caption" for p in batch}, {"input_tokens": 1,
                                                            "output_tokens": 1}
    monkeypatch.setattr(captions_module, "draft_captions", fake)
    monkeypatch.setattr(captions_module, "ai_available", lambda: True)

    c.post("/api/jobs/%s/captions?confirmed=true" % JOB)
    after = names_on_screen(c)
    assert "new one.jpeg" in after, "the caption run removed a photograph"
    assert set(before) <= set(after), "the caption run removed something"


# --- B3: taking one out takes only that one ---------------------------------

def test_taking_one_out_leaves_the_others(client):
    c, job = client
    upload(c, "first.jpeg", (200, 10, 10))
    upload(c, "second.jpeg", (10, 200, 10))
    assert {"first.jpeg", "second.jpeg"} <= set(names_on_screen(c))

    c.post("/api/jobs/%s/photos/first.jpeg/cut" % JOB)

    left = [p for p in c.get("/api/jobs/%s/manifest" % JOB).json()["photos"]
            if not p.get("cut")]
    assert "second.jpeg" in [p["file"] for p in left], \
        "taking one out took the other with it"


# --- B2: no second copy anywhere --------------------------------------------

def test_taking_one_out_leaves_no_copy_behind(client):
    c, job = client
    upload(c, "sign.jpeg")
    before = sorted(p.name for p in (job / "Photos").rglob("*.jpeg"))

    c.post("/api/jobs/%s/photos/sign.jpeg/cut" % JOB)

    after = sorted(p.name for p in (job / "Photos").rglob("*.jpeg"))
    assert after == before, "taking it out changed what is on disk"


def test_adding_the_same_photograph_twice_is_the_only_way_to_get_a_copy(client):
    """`(2)` names are not a fault in themselves: they are what protects a
    photograph that is already there. What was wrong is that the first one
    vanished, so she added it again and again."""
    c, job = client
    upload(c, "sign.jpeg")
    upload(c, "sign.jpeg")
    here = sorted(p.name for p in (job / "Photos" / CHOSEN).glob("sign*"))
    assert here == ["sign (2).jpeg", "sign.jpeg"]


# --- B4: a door out of the blocked build ------------------------------------

def test_a_photograph_that_is_gone_can_be_taken_out(client):
    """The dead end: the list names a photograph that is not there, the build
    refuses, and `Clear captions` refuses too, so there is no way back."""
    c, job = client
    upload(c, "gone.jpeg")
    (job / "Photos" / CHOSEN / "gone.jpeg").unlink()

    r = c.post("/api/jobs/%s/photos/gone.jpeg/cut" % JOB)
    assert r.status_code == 200, "a missing photograph cannot even be taken out"


def test_clearing_captions_still_works_when_a_photograph_has_gone(client):
    """Being unable to start over is worse than the first fault. A job with
    captions must be clearable even when one of its photographs has vanished
    from disk underneath it."""
    c, job = client
    upload(c, "gone.jpeg")
    m = c.get("/api/jobs/%s/manifest" % JOB).json()
    for entry in m["photos"]:
        entry["caption"] = "A caption"
    assert c.put("/api/jobs/%s/manifest" % JOB, json=m).status_code == 200

    (job / "Photos" / CHOSEN / "gone.jpeg").unlink()

    r = c.post("/api/jobs/%s/captions/clear" % JOB)
    assert r.status_code == 200, \
        "she could not even start over: %s" % r.text


# --- and nothing escapes the job --------------------------------------------

def test_an_upload_never_escapes_the_photos_folder(client):
    c, job = client
    upload(c, "../../escape.jpeg")
    assert not (job.parent / "escape.jpeg").exists()
    assert not (job / "escape.jpeg").exists()


def test_a_job_with_no_chosen_folder_still_uses_the_top(client, tmp_path, monkeypatch):
    """Every job the app makes itself is in this state, and it must go on
    behaving exactly as it always has."""
    c, job = client
    jobfacts.forget_photo_folder(job) if hasattr(jobfacts, "forget_photo_folder") else None
    c.put("/api/jobs/%s/photo-group" % JOB, json={"folder": ""})
    upload(c, "top.jpeg")
    assert (job / "Photos" / "top.jpeg").is_file()

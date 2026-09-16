"""A photograph whose file has gone is dropped from the list, not refused.

**What it used to do, and why that was a trap.** The screen quietly drops any
photograph whose file has gone. The build read the manifest file straight off
disk, so it still saw that photograph, and refused with "take that photograph
out, then build again". She could not: the thing it named had no tile on her
screen. Two readings of one list, and she was standing between them.

**What Spenser decided on 2026-09-16.** The build takes it out itself and
carries on. He was given three ways out and chose this one, over showing the
photograph so she could remove it, and over building a report with a gap in it
and saying nothing.

**The removal is written to the file.** A build that skipped it in memory would
refuse again the next time, which is the same trap one run later.

**Nothing appears on her screen about it.** That is a wording decision and it
is his, not this file's. What happens instead is a line in the log, which is
what `Send the log to Spenser` exists to carry.
"""
import io
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import photos            # noqa: E402
from main import create_app   # noqa: E402

JOB = "A JOB"
CHOSEN = "Original Photos_2377 US Highway 6"


@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / "jobs"
    job = home / JOB
    (job / "Photos" / CHOSEN).mkdir(parents=True)
    for i in range(3):
        Image.new("RGB", (40, 30)).save(
            job / "Photos" / CHOSEN / ("IMG_%02d.jpeg" % i))
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    c = TestClient(create_app(), raise_server_exceptions=False)
    c.put("/api/jobs/%s/photo-group" % JOB, json={"folder": CHOSEN})
    # A GET only reads. The file has to exist on disk for this to be the
    # situation at all: the build reads that file directly, which is the
    # whole reason the two readings disagreed.
    photos.save_manifest(job, c.get("/api/jobs/%s/manifest" % JOB).json())
    return c, job


def written(job):
    return json.loads(photos.manifest_path(job).read_text())


def take_the_file_away(job, named="IMG_01.jpeg"):
    """Exactly what happens in the office: somebody moves or deletes the file
    in Windows, with the app none the wiser."""
    (job / "Photos" / CHOSEN / named).unlink()
    return named


def test_the_entry_is_taken_out_of_the_file(client):
    c, job = client
    gone = take_the_file_away(job)
    assert gone in [e["file"] for e in written(job)["photos"]]

    c.post("/api/jobs/%s/build" % JOB)

    assert gone not in [e["file"] for e in written(job)["photos"]], \
        "the dangling entry is still in the manifest, so the next build hits it again"


def test_the_photographs_that_are_there_are_untouched(client):
    c, job = client
    take_the_file_away(job)
    c.post("/api/jobs/%s/build" % JOB)
    left = [e["file"] for e in written(job)["photos"]]
    assert "IMG_00.jpeg" in left and "IMG_02.jpeg" in left


def test_it_does_not_refuse_with_a_sentence_she_cannot_act_on(client):
    c, job = client
    take_the_file_away(job)
    answer = c.post("/api/jobs/%s/build" % JOB)
    assert answer.status_code != 400 or "photo list but the file" not in \
        str(answer.json().get("detail", "")), \
        "it still names a photograph that has no tile on her screen"


def test_a_second_build_finds_nothing_to_take_out(client):
    """The trap was that the refusal came back every time. Once is a tidy-up;
    twice would mean nothing was written down."""
    c, job = client
    take_the_file_away(job)
    c.post("/api/jobs/%s/build" % JOB)
    before = written(job)
    c.post("/api/jobs/%s/build" % JOB)
    assert written(job)["photos"] == before["photos"]


def test_it_is_written_to_the_log(client, monkeypatch):
    """Nothing is said on screen, so the log is the only record that a
    photograph left her report. It has to be there."""
    import applog
    said = []
    monkeypatch.setattr(applog, "note",
                        lambda message, **fields: said.append((message, fields)))
    c, job = client
    gone = take_the_file_away(job)
    c.post("/api/jobs/%s/build" % JOB)
    assert any(gone in str(fields) for _, fields in said), \
        "a photograph was taken out of her report and nothing recorded it"


def test_nothing_is_written_when_every_file_is_there(client):
    c, job = client
    before = written(job)
    c.post("/api/jobs/%s/build" % JOB)
    assert written(job)["photos"] == before["photos"]

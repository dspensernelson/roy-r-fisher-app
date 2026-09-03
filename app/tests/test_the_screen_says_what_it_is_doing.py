"""The photo screen says what it is doing, and never sits on `Loading...`.

Two faults, one screen, and the second one is the reason Colleen lost a
morning on 2026-09-03.

**It says nothing while it works.** A slow screen and a dead screen looked
identical. The rule was already on record from 2026-08-28, about the update
download: a bar that says nothing looks like a hang, because the jobs are on a
network drive. The photo screen never got it.

**It hides the reason when it fails.** `PhotosScreen.jsx:216` returns
`Loading...` whenever there is no manifest. The lines that display an error sit
at 240, 277 and 607, all below it. So a failed read was caught, stored in
state, and then never reached. The screen sat there holding the explanation in
its pocket. Her log:

    10:48:57  GET .../manifest  status=400
    10:50:33  GET .../manifest  status=400

The only way out was deleting `photo-manifest.json` by hand, which risked every
caption in the job.
"""
import sys
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import photos  # noqa: E402
import progress  # noqa: E402
from main import create_app  # noqa: E402

JOB = "A JOB"


@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / "jobs"
    job = home / JOB
    (job / "Photos").mkdir(parents=True)
    for i in range(6):
        Image.new("RGB", (40, 30)).save(job / "Photos" / ("IMG_%04d.jpeg" % i))
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    return TestClient(create_app(), raise_server_exceptions=False), job


# --- the count the screen shows ---------------------------------------------

def test_reading_starts_at_nothing(client):
    c, job = client
    at = c.get("/api/jobs/%s/reading" % JOB).json()
    assert at["reading"] is False
    assert at["done"] == 0 and at["total"] == 0


def test_the_route_never_reads_the_photographs_itself(client, monkeypatch):
    """It is polled every second while another call is already doing the slow
    work. If it did the slow work too it would make the wait worse."""
    called = []
    real = photos.load_manifest
    monkeypatch.setattr(photos, "load_manifest",
                        lambda job: called.append(1) or real(job))
    c, job = client
    c.get("/api/jobs/%s/reading" % JOB)
    assert called == [], "the progress route read the whole job"


def test_a_read_reports_its_position_as_it_goes(client):
    c, job = client
    seen = []

    def watch(name, done, total):
        seen.append((done, total))

    real_advance = progress.read_advance
    progress.read_advance = watch
    try:
        c.get("/api/jobs/%s/manifest" % JOB)
    finally:
        progress.read_advance = real_advance

    assert seen, "nothing reported its position while it worked"
    assert seen[-1][1] == 6, "it did not say how many there were"
    assert [d for d, _ in seen] == sorted(d for d, _ in seen), "the count went backwards"


def test_the_count_is_cleared_when_the_read_ends(client):
    c, job = client
    c.get("/api/jobs/%s/manifest" % JOB)
    at = c.get("/api/jobs/%s/reading" % JOB).json()
    assert at["reading"] is False, "it still says it is reading after it finished"


def test_a_caption_run_and_a_read_do_not_overwrite_each_other(client):
    """One dictionary with one entry per job would let a read wipe a caption
    run's position, and the caption poller refetches the manifest while a run
    is going, so this collision is real rather than theoretical."""
    c, job = client
    progress.start(JOB, total=12, requests=2)
    progress.advance(JOB, request=1, captioned=5)

    progress.read_start(JOB, total=6)
    progress.read_advance(JOB, done=3, total=6)
    progress.read_finish(JOB)

    still = progress.read(JOB)
    assert still["running"] is True, "the read wiped the caption run"
    assert still["captioned"] == 5 and still["request"] == 1
    progress.finish(JOB)


def test_the_count_survives_a_read_that_fails(client):
    """However a read ends, the light goes out. A stuck light leaves the
    screen polling for ever."""
    c, job = client
    (job / "Photos" / "photo-manifest.json").write_text("{ this is not json")
    c.get("/api/jobs/%s/manifest" % JOB)
    at = c.get("/api/jobs/%s/reading" % JOB).json()
    assert at["reading"] is False


# --- and the error is not hidden --------------------------------------------

def test_an_unreadable_photo_list_is_reported_not_swallowed(client):
    """This is Colleen's morning. The list could not be read, and the screen
    showed `Loading...` for ever rather than the reason."""
    c, job = client
    (job / "Photos" / "photo-manifest.json").write_text("{ this is not json")
    r = c.get("/api/jobs/%s/manifest" % JOB)
    assert r.status_code == 400
    assert "photo-manifest.json" in r.json()["detail"]

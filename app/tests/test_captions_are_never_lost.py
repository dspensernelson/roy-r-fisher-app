"""A spare copy of the captions survives every save, and a failed save
never damages the file Mark's report is built from.

`save_manifest` in `app/server/photos.py` used to write the manifest with a
plain `path.write_text`: no temporary file, no previous copy kept. This proves
both are fixed: `state.write_text` makes a failed write leave the old file
untouched, and `captionbackup.keep` makes the version from before every save
recoverable on its own, outside the job folder.
"""
import io
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import captionbackup  # noqa: E402
import state  # noqa: E402
import thumbcache  # noqa: E402
from main import create_app  # noqa: E402


def jpg_bytes(color):
    buf = io.BytesIO()
    Image.new("RGB", (320, 240), color).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / "jobs"
    (home / "JOB1" / "Photos").mkdir(parents=True)
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    return TestClient(create_app(), raise_server_exceptions=False), home / "JOB1"


def test_a_save_writes_a_spare_holding_what_was_there_before(client):
    c, job = client
    c.post("/api/jobs/JOB1/photos", files=[
        ("files", ("a.jpg", jpg_bytes((1, 1, 1)), "image/jpeg")),
    ])
    m = c.get("/api/jobs/JOB1/manifest").json()
    m["photos"][0]["caption"] = "First caption"
    assert c.put("/api/jobs/JOB1/manifest", json=m).status_code == 200

    m2 = c.get("/api/jobs/JOB1/manifest").json()
    m2["photos"][0]["caption"] = "Second caption"
    assert c.put("/api/jobs/JOB1/manifest", json=m2).status_code == 200

    spare = captionbackup.spare_for(job / "Photos")
    assert spare.is_file()
    saved = json.loads(spare.read_text())
    # The spare holds the version from before the most recent save, so it
    # carries the first caption, not the second.
    assert saved["photos"][0]["caption"] == "First caption"


def test_two_saves_in_a_row_leave_the_second_to_last_version(client):
    c, job = client
    c.post("/api/jobs/JOB1/photos", files=[
        ("files", ("a.jpg", jpg_bytes((1, 1, 1)), "image/jpeg")),
    ])
    for word in ("one", "two", "three"):
        m = c.get("/api/jobs/JOB1/manifest").json()
        m["photos"][0]["caption"] = word
        c.put("/api/jobs/JOB1/manifest", json=m)

    spare = captionbackup.spare_for(job / "Photos")
    saved = json.loads(spare.read_text())
    assert saved["photos"][0]["caption"] == "two"


def test_a_failed_write_leaves_the_original_file_untouched(client, monkeypatch):
    c, job = client
    c.post("/api/jobs/JOB1/photos", files=[
        ("files", ("a.jpg", jpg_bytes((1, 1, 1)), "image/jpeg")),
    ])
    m = c.get("/api/jobs/JOB1/manifest").json()
    m["photos"][0]["caption"] = "Safe caption"
    c.put("/api/jobs/JOB1/manifest", json=m)

    before = (job / "Photos" / "photo-manifest.json").read_text()

    def boom(*a, **k):
        raise OSError("disk is gone")
    monkeypatch.setattr(state, "write_text", boom)

    m2 = c.get("/api/jobs/JOB1/manifest").json()
    m2["photos"][0]["caption"] = "This must not land"
    r = c.put("/api/jobs/JOB1/manifest", json=m2)
    assert r.status_code >= 500

    after = (job / "Photos" / "photo-manifest.json").read_text()
    assert after == before


def test_no_temporary_file_survives_a_failed_save(client, monkeypatch):
    """Uses the real `state.write_text`, not a stand-in, so its own cleanup
    runs. Only the last step, the rename that makes the new file real, fails."""
    c, job = client
    c.post("/api/jobs/JOB1/photos", files=[
        ("files", ("a.jpg", jpg_bytes((1, 1, 1)), "image/jpeg")),
    ])

    import os
    real_replace = os.replace

    def boom_replace(src, dst):
        if str(dst).endswith("photo-manifest.json"):
            raise OSError("interrupted")
        return real_replace(src, dst)
    monkeypatch.setattr(os, "replace", boom_replace)

    m = c.get("/api/jobs/JOB1/manifest").json()
    m["photos"][0]["caption"] = "will not land"
    r = c.put("/api/jobs/JOB1/manifest", json=m)
    assert r.status_code >= 500

    leftovers = list((job / "Photos").glob("*.writing"))
    assert leftovers == []


def test_a_caption_outside_the_chosen_folder_still_survives_a_save(client):
    c, job = client
    c.post("/api/jobs/JOB1/photos", files=[
        ("files", ("a.jpg", jpg_bytes((1, 1, 1)), "image/jpeg")),
        ("files", ("b.jpg", jpg_bytes((2, 2, 2)), "image/jpeg")),
    ])
    # Both photographs are saved once, with b captioned, while both are
    # still visible to the screen.
    m = c.get("/api/jobs/JOB1/manifest").json()
    for p in m["photos"]:
        if p["file"] == "b.jpg":
            p["caption"] = "Kept even though it's off-screen"
    assert c.put("/api/jobs/JOB1/manifest", json=m).status_code == 200

    # Now the screen saves again, showing only a.jpg, as it would after he
    # chose a folder that no longer includes b.jpg.
    c.put("/api/jobs/JOB1/manifest", json={
        "photos": [p for p in m["photos"] if p["file"] == "a.jpg"],
    })

    stored = json.loads((job / "Photos" / "photo-manifest.json").read_text())
    kept = [p for p in stored["photos"] if p["file"] == "b.jpg"]
    assert kept and kept[0]["caption"] == "Kept even though it's off-screen"


def test_the_spare_never_lands_inside_the_job_folder(client):
    c, job = client
    c.post("/api/jobs/JOB1/photos", files=[
        ("files", ("a.jpg", jpg_bytes((1, 1, 1)), "image/jpeg")),
    ])
    m = c.get("/api/jobs/JOB1/manifest").json()
    m["photos"][0]["caption"] = "x"
    c.put("/api/jobs/JOB1/manifest", json=m)

    spare = captionbackup.spare_for(job / "Photos")
    assert thumbcache.cache_root() in spare.parents
    assert job not in spare.parents

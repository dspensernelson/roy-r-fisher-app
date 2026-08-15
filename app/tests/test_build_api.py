import json
import sys
from pathlib import Path

import pytest
from docx import Document
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
from main import create_app  # noqa: E402
from conftest import TEMPLATE_DOCX, has_template  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / "jobs"
    (home / "JOB1" / "Photos").mkdir(parents=True)
    Image.new("RGB", (300, 200), (9, 9, 9)).save(home / "JOB1" / "Photos" / "a.jpg")
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    monkeypatch.setenv("RRF_PHOTO_TEMPLATE", str(TEMPLATE_DOCX))
    c = TestClient(create_app())
    m = c.get("/api/jobs/JOB1/manifest").json()
    m["photos"] = [{"file": "a.jpg", "caption": "View of test"}]
    m["report_year"] = 2026
    c.put("/api/jobs/JOB1/manifest", json=m)
    return c, home / "JOB1"


@has_template
def test_build_creates_docx(client):
    c, job = client
    r = c.post("/api/jobs/JOB1/build")
    assert r.status_code == 200, r.text
    created = r.json()["created"]
    out = job / "Photos" / created
    assert out.exists()
    assert len(Document(str(out)).inline_shapes) == 1


@has_template
def test_build_error_surfaces_real_message(client):
    c, job = client
    m = c.get("/api/jobs/JOB1/manifest").json()
    m["photos"] = [{"file": "missing.jpg", "caption": "x"}]
    c.put("/api/jobs/JOB1/manifest", json=m)
    r = c.post("/api/jobs/JOB1/build")
    assert r.status_code == 500
    assert "missing.jpg" in r.json()["detail"]


def test_build_no_manifest_gives_plain_english_error(client, tmp_path, monkeypatch):
    """A job that never had photos uploaded/manifested at all -- no
    photo-manifest.json on disk yet. The refusal must read as plain
    English, not jargon, per the house rule on error text.
    """
    home = tmp_path / "jobs2"
    (home / "JOB2" / "Photos").mkdir(parents=True)
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    monkeypatch.setenv("RRF_PHOTO_TEMPLATE", str(TEMPLATE_DOCX))
    c = TestClient(create_app())
    r = c.post("/api/jobs/JOB2/build")
    assert r.status_code == 400
    assert "photo" in r.json()["detail"].lower()


@has_template
def test_build_with_photos_but_no_manifest_file_succeeds(tmp_path, monkeypatch):
    """The appraiser's real workflow: dump camera photos straight into the
    job's Photos folder, then open the app and hit Build -- often before
    the app has ever touched this job, so there is no photo-manifest.json
    on disk at all yet. The build endpoint must reconcile against the
    folder the same way GET /manifest does, rather than reading "no
    manifest file" as "no photos," and must produce a document containing
    those photos.
    """
    home = tmp_path / "jobs3"
    photos_dir = home / "JOB3" / "Photos"
    photos_dir.mkdir(parents=True)
    Image.new("RGB", (300, 200), (40, 80, 120)).save(photos_dir / "one.jpg")
    Image.new("RGB", (300, 200), (120, 40, 80)).save(photos_dir / "two.jpg")
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    monkeypatch.setenv("RRF_PHOTO_TEMPLATE", str(TEMPLATE_DOCX))

    assert not (photos_dir / "photo-manifest.json").is_file()

    c = TestClient(create_app())
    r = c.post("/api/jobs/JOB3/build")
    assert r.status_code == 200, r.text
    created = r.json()["created"]
    out = photos_dir / created
    assert out.exists()
    assert len(Document(str(out)).inline_shapes) == 2


def test_build_rejects_hand_written_manifest_escape(client, tmp_path):
    """The manifest file also sits on disk where a human or another
    process can edit it directly -- bypassing PUT /manifest entirely, so
    PUT's own validation never runs. Hand-write a photo-manifest.json
    whose photos[].file is a bare name ("evil.jpg", no "../", no path
    separators) that is actually a symlink resolving outside the Photos
    folder, then hit the build endpoint directly.

    This is exactly the attack shape a naive "reject strings containing
    ../ " check would miss -- the string is clean, only the resolved,
    on-disk target escapes. The build endpoint must re-validate with the
    same resolve-based helper PUT uses (_validate_manifest_shape) before
    ever handing the manifest to the engine, which does
    `photos_dir / entry["file"]` with no safety check of its own.

    Must refuse with a clear error and must not produce any document.
    """
    c, job = client
    photos_dir = job / "Photos"

    outside_secret = tmp_path / "outside-secret.txt"
    outside_secret.write_text("not a photo; must never be opened by the engine")

    escape_link = photos_dir / "evil.jpg"
    escape_link.symlink_to(outside_secret)

    manifest_file = photos_dir / "photo-manifest.json"
    manifest_file.write_text(json.dumps({
        "job": "JOB1",
        "context": "",
        "report_year": 2026,
        "photos": [{"file": "evil.jpg", "caption": "x"}],
    }))

    before = set(photos_dir.iterdir())
    r = c.post("/api/jobs/JOB1/build")

    assert r.status_code == 400, r.text
    assert "outside the Photos folder" in r.json()["detail"]

    after = set(photos_dir.iterdir())
    assert after == before, "build must not write any file when the manifest is rejected"

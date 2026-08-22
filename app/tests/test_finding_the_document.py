"""The finished document is easy to find, and the cache is out of his folder.

Two findings from the audit, both at the end of the journey.

Build said the file was created "in this job's Photos folder" and stopped
there, so the last step of the whole workflow was leaving the app and hunting
for it in Explorer. It now offers to open the document or show it in its
folder, and does neither on its own.

The thumbnail cache was being written inside the job's own Photos folder, next
to his client's photographs, with doubled names like `photo-01.jpg.jpg`. It now
lives in app-owned storage. Old caches are left exactly where they are.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import jobs as jobs_module  # noqa: E402
import reveal  # noqa: E402
import thumbcache  # noqa: E402
from main import create_app  # noqa: E402

WEB = Path(__file__).resolve().parents[1] / "web" / "src"
PIXEL = Path(__file__).resolve().parent / "fixtures"


def a_photo() -> bytes:
    """A real JPEG, small, made here so no fixture file is needed."""
    import io

    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (40, 30), (120, 90, 60)).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path / "jobs"))
    monkeypatch.setenv("RRF_CACHE_DIR", str(tmp_path / "cache"))
    job = tmp_path / "jobs" / "ANYTOWN_1 Main Street - 2026"
    for folder in jobs_module.MARK_FOLDERS:
        (job / folder).mkdir(parents=True)
    (job / "Photos" / "photo-01.jpg").write_bytes(a_photo())
    (job / "Photos" / "photo-manifest.json").write_text(json.dumps(
        {"job": job.name, "context": "", "report_year": 2026, "caption_style": "view",
         "photos": [{"file": "photo-01.jpg", "caption": "View of the front", "reviewed": True}]},
        indent=2))
    return job


@pytest.fixture
def client(home):
    return TestClient(create_app(), raise_server_exceptions=False)


JOB = "ANYTOWN_1 Main Street - 2026"


# --- the cache is not in his folder --------------------------------------
def test_a_thumbnail_writes_nothing_into_the_job(client, home):
    before = sorted(p.name for p in (home / "Photos").iterdir())
    assert client.get("/api/jobs/%s/thumb/photo-01.jpg" % JOB).status_code == 200
    after = sorted(p.name for p in (home / "Photos").iterdir())
    assert after == before, "the job folder is unchanged by drawing a thumbnail"
    assert not (home / "Photos" / ".rrf-thumbs").exists()


def test_the_thumbnail_lands_in_app_owned_storage(client, tmp_path):
    client.get("/api/jobs/%s/thumb/photo-01.jpg" % JOB)
    cached = list((tmp_path / "cache").rglob("*.jpg"))
    assert len(cached) == 1


def test_the_extension_is_replaced_not_doubled(client, tmp_path):
    client.get("/api/jobs/%s/thumb/photo-01.jpg" % JOB)
    name = next((tmp_path / "cache").rglob("*.jpg")).name
    assert not name.endswith(".jpg.jpg")
    assert name.startswith("photo-01-")


def test_two_photos_that_differ_only_by_extension_do_not_collide(tmp_path):
    photos = tmp_path / "Photos"
    photos.mkdir()
    one = thumbcache.cached_file(photos, "roof.jpg")
    two = thumbcache.cached_file(photos, "roof.png")
    assert one != two


def test_the_same_job_name_in_two_workspaces_gets_two_caches(tmp_path):
    a = tmp_path / "one" / "A job" / "Photos"
    b = tmp_path / "two" / "A job" / "Photos"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    assert thumbcache.cached_file(a, "x.jpg") != thumbcache.cached_file(b, "x.jpg")


def test_a_changed_photograph_is_noticed(client, home, tmp_path):
    client.get("/api/jobs/%s/thumb/photo-01.jpg" % JOB)
    cached = next((tmp_path / "cache").rglob("*.jpg"))
    old = cached.stat().st_mtime
    source = home / "Photos" / "photo-01.jpg"
    source.write_bytes(a_photo())
    import os
    os.utime(source, (old + 100, old + 100))
    assert thumbcache.is_stale(cached, source)


def test_an_old_cache_in_the_job_is_left_alone(client, home):
    """Not deleted from one of his folders as a side effect of a fix."""
    stale = home / "Photos" / ".rrf-thumbs"
    stale.mkdir()
    (stale / "photo-01.jpg.jpg").write_bytes(b"old")
    client.get("/api/jobs/%s/thumb/photo-01.jpg" % JOB)
    assert (stale / "photo-01.jpg.jpg").read_bytes() == b"old"


def test_the_app_works_with_no_old_cache_present(client, home):
    assert not (home / "Photos" / ".rrf-thumbs").exists()
    assert client.get("/api/jobs/%s/thumb/photo-01.jpg" % JOB).status_code == 200


def test_an_old_cache_is_still_never_listed_as_a_folder_of_his(client, home):
    (home / "Photos" / ".rrf-thumbs").mkdir()
    body = client.get("/api/jobs/%s/folders" % JOB).json()
    every = [f["folder"] for f in body["typical"] + body["other"]]
    assert ".rrf-thumbs" not in every


# --- opening the finished document ---------------------------------------
def test_opening_is_offered_and_never_automatic(monkeypatch, client, home):
    opened = []
    monkeypatch.setattr(reveal, "open_document", lambda p: opened.append(Path(p)))
    built = home / "Photos" / "Anytown_1 Main Street Photos (Complete).docx"
    built.write_bytes(b"a document")

    assert opened == [], "nothing opens until he asks"
    answer = client.post("/api/jobs/%s/reveal" % JOB,
                         json={"file": built.name, "what": "document"})
    assert answer.status_code == 200
    assert opened == [built]


def test_showing_in_the_folder_picks_out_that_file(monkeypatch, client, home):
    shown = []
    monkeypatch.setattr(reveal, "show_in_folder", lambda p: shown.append(Path(p)))
    built = home / "Photos" / "Anytown_1 Main Street Photos (Complete).docx"
    built.write_bytes(b"a document")

    client.post("/api/jobs/%s/reveal" % JOB, json={"file": built.name, "what": "folder"})
    assert shown == [built]


def test_a_file_outside_the_job_cannot_be_opened(monkeypatch, client, tmp_path):
    opened = []
    monkeypatch.setattr(reveal, "open_document", lambda p: opened.append(p))
    outside = tmp_path / "secrets.docx"
    outside.write_bytes(b"not his")
    answer = client.post("/api/jobs/%s/reveal" % JOB,
                         json={"file": "../../secrets.docx", "what": "document"})
    assert answer.status_code == 404
    assert opened == []


def test_a_refusal_to_open_never_says_the_build_failed(monkeypatch, client, home):
    def refuse(_path):
        raise reveal.RevealFailed("This computer would not open it.")
    monkeypatch.setattr(reveal, "open_document", refuse)
    built = home / "Photos" / "Anytown_1 Main Street Photos (Complete).docx"
    built.write_bytes(b"a document")

    answer = client.post("/api/jobs/%s/reveal" % JOB,
                         json={"file": built.name, "what": "document"})
    assert answer.status_code == 409
    detail = answer.json()["detail"]
    assert str(built) in detail, "it says where the file is"
    assert "fail" not in detail.lower() or "build" not in detail.lower()


def test_neither_call_uses_a_shell():
    """A job folder name is arbitrary text and must never be parsed by one."""
    source = (Path(__file__).resolve().parents[1] / "server" / "reveal.py").read_text()
    assert "shell=True" not in source
    assert "os.system" not in source


# --- the screen -----------------------------------------------------------
def test_the_screen_offers_both_actions_and_calls_neither_on_its_own():
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert ">Open document<" in screen
    assert ">Show in folder<" in screen
    assert 'onClick={() => onReveal("document")}' in screen
    assert 'onClick={() => onReveal("folder")}' in screen
    # the shape of the defect: revealing from the build handler itself
    build_fn = screen[screen.index("async function onBuild()"):]
    build_fn = build_fn[:build_fn.index("async function onReveal")]
    assert "onReveal" not in build_fn


def test_the_two_success_boxes_are_not_both_on_screen():
    """`Will be saved as` disappears once the file actually exists."""
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert "{facts && inPhotos.length > 0 && !done && (" in screen

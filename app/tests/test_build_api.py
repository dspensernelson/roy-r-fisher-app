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


def ready_to_build(c, job_name: str) -> None:
    """Everything Build has required since these tests were last able to run.

    They predate two gates and never noticed either, because the corpus they
    need moved next door when the repository was split, and they skipped from
    then until 2026-08-22. Build now insists on a caption for every included
    photograph, a tick against each one, and a city and street address to name
    the file from. This does what Mark does, in that order.
    """
    manifest = c.get("/api/jobs/%s/manifest" % job_name).json()
    for n, photo in enumerate(manifest["photos"], start=1):
        if not str(photo.get("caption", "")).strip():
            photo["caption"] = "View of the test subject %d" % n
    c.put("/api/jobs/%s/manifest" % job_name, json=manifest)
    c.put("/api/jobs/%s/facts" % job_name,
          json={"city": "Davenport", "address": "1 Test Street"})
    for photo in manifest["photos"]:
        c.post("/api/jobs/%s/photos/%s/reviewed" % (job_name, photo["file"]))


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
    ready_to_build(c, "JOB1")
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
def test_a_dangling_entry_is_taken_out_and_the_build_carries_on(client, tmp_path):
    """A photograph whose file has gone leaves the list, and the report builds.

    **This test asserted the opposite until 2026-09-16.** It required a 400
    naming the photograph and saying "Take that photograph out", and it called
    that refusal honest. It was not: `load_manifest` had already dropped that
    entry before the screen saw it, so the photograph she was told to take out
    had no tile to take out. She was being handed an instruction she could not
    follow.

    Spenser chose the removal on 2026-09-16, over showing the photograph so she
    could take it out herself, and over building with a gap and saying nothing.

    The state is still reached the same way, and that part of the old note
    stands: the manifest file sits on disk where a person or another process
    can edit it, and the build reads that raw file rather than the
    reconciliation, which is what makes a genuinely dangling entry reachable at
    all.
    """
    c, job = client
    photos = job / "Photos"
    manifest = photos / "photo-manifest.json"
    manifest.write_text(json.dumps({
        "job": "JOB1", "context": "", "report_year": 2026, "caption_style": "view",
        "photos": [
            {"file": "a.jpg", "caption": "View of the front", "reviewed": True},
            {"file": "missing.jpg", "caption": "View of nothing", "reviewed": True},
        ]}), encoding="utf-8")

    r = c.post("/api/jobs/JOB1/build")

    assert r.status_code == 200, "it refused over a photograph she cannot reach"
    left = [e["file"] for e in json.loads(manifest.read_text())["photos"]]
    assert "missing.jpg" not in left, "the entry is still there for the next build"
    assert "a.jpg" in left, "a photograph that is really there was taken out"
    assert list(photos.glob("*.docx")), "the report was not built"


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
    ready_to_build(c, "JOB3")
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


# --- the layout the job chose actually reaches the document ---------------

@pytest.fixture
def six_photo_job(tmp_path, monkeypatch):
    """A job with six photographs and no RRF_PHOTO_TEMPLATE override, so the
    server picks the shipped template for itself. That choice is the thing
    under test and an override would hide it."""
    home = tmp_path / "jobs"
    photos = home / "JOB1" / "Photos"
    photos.mkdir(parents=True)
    for i in range(6):
        Image.new("RGB", (400, 300), (i * 40 % 255, 9, 9)).save(photos / f"p{i}.jpg")
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    monkeypatch.delenv("RRF_PHOTO_TEMPLATE", raising=False)
    c = TestClient(create_app())
    m = c.get("/api/jobs/JOB1/manifest").json()
    m["photos"] = [{"file": f"p{i}.jpg", "caption": f"View of test subject {i}"}
                   for i in range(6)]
    m["report_year"] = 2026
    c.put("/api/jobs/JOB1/manifest", json=m)
    ready_to_build(c, "JOB1")
    return c, photos


def _built(c, photos):
    r = c.post("/api/jobs/JOB1/build")
    assert r.status_code == 200, r.text
    return Document(str(photos / r.json()["created"]))


def test_a_job_that_never_chose_builds_three_per_page(six_photo_job):
    """Absent means three. Six photographs are two three-up pages."""
    c, photos = six_photo_job
    d = _built(c, photos)
    assert len(d.tables) == 2
    assert [len(t.rows) for t in d.tables] == [3, 3]
    assert len(d.inline_shapes) == 6


def test_choosing_six_builds_one_page_of_six(six_photo_job):
    """The same six photographs, one page, captions beneath rather than
    beside. This is the whole feature, end to end through the endpoint."""
    c, photos = six_photo_job
    m = c.get("/api/jobs/JOB1/manifest").json()
    m["photos_per_page"] = 6
    assert c.put("/api/jobs/JOB1/manifest", json=m).status_code == 200

    d = _built(c, photos)
    assert len(d.tables) == 1
    assert len(d.tables[0].rows) == 6 and len(d.tables[0].columns) == 2
    assert len(d.inline_shapes) == 6
    # Captions on the odd rows, photographs on the even ones.
    t = d.tables[0]
    assert [t.rows[r].cells[c_].text.strip() for r, c_ in
            ((1, 0), (1, 1), (3, 0), (3, 1), (5, 0), (5, 1))] == \
           [f"View of test subject {i}" for i in range(6)]

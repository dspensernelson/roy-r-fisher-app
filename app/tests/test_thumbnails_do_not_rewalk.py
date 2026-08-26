"""Showing a photograph must not search the whole job for it.

Mark's jobs live on a mapped network drive. Every filesystem question the app
asks there is a request to another machine, so the cost of a screen is the
number of questions it asks, not the work it does.

Measured 2026-08-26 on the Mason City job, 57 photographs: opening the photo
screen made 6,954 path lookups, because each thumbnail asked "where is this
photograph" and the app answered by walking the entire Photos tree again. On a
local disk that is a tenth of a second and invisible. Over a network drive at
two milliseconds a call it is fourteen seconds, and at five it is thirty-five.

Nothing about that is visible on the machine this is developed on, which is why
it is a test that counts calls rather than one that measures time. A timing
test here would pass on a fast disk forever and never say anything true about
his.

The app already records where each photograph sits, in the manifest, so the
answer is a file read rather than a search. The walk stays as the fallback for
a photograph the manifest does not know about, so nothing that used to work
stops working.
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import jobs  # noqa: E402
import photos  # noqa: E402


def a_photo(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (80, 60), (60, 110, 160)).save(path)
    return path


def a_job(tmp_path: Path, *rels: str) -> Path:
    job = tmp_path / "DAVENPORT_1 Test Street"
    for rel in rels:
        a_photo(job / "Photos" / rel)
    return job


def client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import main
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path))
    return TestClient(main.create_app())


class Counter:
    """Counts full recursive walks of a job's Photos tree."""

    def __init__(self, monkeypatch):
        self.walks = 0
        real = jobs._walk_photos
        def counted(root):
            self.walks += 1
            return real(root)
        monkeypatch.setattr(jobs, "_walk_photos", counted)


def a_job_with_a_saved_manifest(tmp_path, n=12):
    rels = ["Raw pics_X/IMG_%04d.jpeg" % i for i in range(n)]
    job = a_job(tmp_path, *rels)
    photos.save_manifest(job, photos.load_manifest(job))
    return job, [Path(r).name for r in rels]


# --- the defect itself ----------------------------------------------------
def test_showing_every_photograph_does_not_walk_the_job_every_time(tmp_path, monkeypatch):
    job, names = a_job_with_a_saved_manifest(tmp_path)
    c = client(tmp_path, monkeypatch)
    count = Counter(monkeypatch)
    for name in names:
        assert c.get("/api/jobs/DAVENPORT_1 Test Street/thumb/%s" % name).status_code == 200
    assert count.walks == 0, (
        "twelve thumbnails walked the tree %d times. On his network drive each "
        "walk is hundreds of requests to another machine." % count.walks)


def test_one_thumbnail_costs_no_walk_at_all(tmp_path, monkeypatch):
    job, names = a_job_with_a_saved_manifest(tmp_path, n=1)
    c = client(tmp_path, monkeypatch)
    count = Counter(monkeypatch)
    c.get("/api/jobs/DAVENPORT_1 Test Street/thumb/%s" % names[0])
    assert count.walks == 0


# --- and it still finds everything it used to -----------------------------
def test_a_photograph_in_a_subfolder_is_still_served(tmp_path, monkeypatch):
    job, names = a_job_with_a_saved_manifest(tmp_path, n=2)
    c = client(tmp_path, monkeypatch)
    answer = c.get("/api/jobs/DAVENPORT_1 Test Street/thumb/%s" % names[0])
    assert answer.status_code == 200
    assert answer.headers["content-type"] == "image/jpeg"


def test_a_photograph_the_manifest_has_never_seen_is_still_found(tmp_path, monkeypatch):
    """The fallback. A photograph dropped into the folder a moment ago is not
    in the saved manifest yet, and it must still show."""
    job, _ = a_job_with_a_saved_manifest(tmp_path, n=1)
    a_photo(jobs.photos_dir(job) / "Raw pics_X" / "BRAND_NEW.jpeg")
    c = client(tmp_path, monkeypatch)
    assert c.get("/api/jobs/DAVENPORT_1 Test Street/thumb/BRAND_NEW.jpeg").status_code == 200


def test_a_job_with_no_manifest_at_all_still_serves_thumbnails(tmp_path, monkeypatch):
    a_job(tmp_path, "Raw pics_X/one.jpeg")
    c = client(tmp_path, monkeypatch)
    assert c.get("/api/jobs/DAVENPORT_1 Test Street/thumb/one.jpeg").status_code == 200


def test_a_photograph_at_the_top_of_photos_still_works(tmp_path, monkeypatch):
    job = a_job(tmp_path, "loose.jpg")
    photos.save_manifest(job, photos.load_manifest(job))
    c = client(tmp_path, monkeypatch)
    assert c.get("/api/jobs/DAVENPORT_1 Test Street/thumb/loose.jpg").status_code == 200


def test_a_photograph_that_is_gone_is_still_a_404(tmp_path, monkeypatch):
    a_job(tmp_path, "Raw pics_X/one.jpeg")
    c = client(tmp_path, monkeypatch)
    assert c.get("/api/jobs/DAVENPORT_1 Test Street/thumb/nothere.jpeg").status_code == 404


def test_a_manifest_naming_a_file_that_has_gone_is_a_404_not_a_crash(tmp_path, monkeypatch):
    """The manifest is hand-editable, so it can name something that is not
    there. Trusting it without checking would hand Image.open a missing path."""
    job, names = a_job_with_a_saved_manifest(tmp_path, n=1)
    (jobs.photos_dir(job) / "Raw pics_X" / names[0]).unlink()
    c = client(tmp_path, monkeypatch)
    assert c.get("/api/jobs/DAVENPORT_1 Test Street/thumb/%s" % names[0]).status_code == 404


# --- the confinement is not weakened --------------------------------------
def test_a_manifest_folder_that_climbs_out_is_refused(tmp_path, monkeypatch):
    """The folder now comes from a hand-editable file, so it is confined on the
    way out exactly as the walk's own answer always was."""
    import json
    job = a_job(tmp_path, "Raw pics_X/one.jpeg")
    secret = tmp_path / "elsewhere"
    a_photo(secret / "secret.jpeg")
    photos.manifest_path(job).write_text(json.dumps({
        "job": job.name, "context": "", "report_year": 2026,
        "photos": [{"file": "secret.jpeg", "folder": "../../elsewhere",
                    "caption": ""}]}))
    c = client(tmp_path, monkeypatch)
    assert c.get("/api/jobs/DAVENPORT_1 Test Street/thumb/secret.jpeg").status_code == 404


def test_a_link_out_of_photos_is_still_refused(tmp_path, monkeypatch):
    import pytest
    job = a_job(tmp_path, "one.jpeg")
    outside = tmp_path / "elsewhere"
    a_photo(outside / "secret.jpeg")
    try:
        (jobs.photos_dir(job) / "escape.jpeg").symlink_to(outside / "secret.jpeg")
    except (OSError, NotImplementedError):
        pytest.skip("this filesystem does not do symlinks")
    c = client(tmp_path, monkeypatch)
    assert c.get("/api/jobs/DAVENPORT_1 Test Street/thumb/escape.jpeg").status_code == 404

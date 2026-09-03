"""A photograph's capture time is read once, not on every click.

Measured on 2026-09-02 on the Blaul Lofts job: one click of `Mark Reviewed`
opened 130 photograph files. Measured again on 2026-09-03 from Colleen's own
machine in Mark's office, on a job of 40 photographs over a network drive,
where the same waste showed up as this, over and over:

    GET .../caption-estimate  status=200  ms=11374
    GET .../caption-estimate  status=200  ms=10031
    GET .../caption-estimate  status=200  ms=9415

`load_manifest` hands every file it does not know to `exif_order`, which opens
each one to read its capture date and then throws the answer away, because
`load_manifest` never writes back. That is deliberate and stays: a plain read
must not have a side effect. So the dates go in a cache beside the list and
never inside it, which is why this change cannot cost anybody a caption.

**These count file opens rather than measuring time.** A timing test passes for
ever on a fast disk and says nothing true about a network drive in Davenport.
Same discipline as `test_thumbnails_do_not_rewalk.py`, which exists for exactly
this reason.
"""
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "engine"))
import capturedates  # noqa: E402
import jobs  # noqa: E402
import photo_pages  # noqa: E402
import photos  # noqa: E402
import thumbcache  # noqa: E402
from main import create_app  # noqa: E402

JOB = "A JOB"


class Opens:
    """Counts how many photograph files are opened to read a capture date.

    Wraps `PIL.Image.open` and delegates, so behaviour is unchanged and only
    the count is new. Built after the client and after any warm-up, so setup
    is never counted.
    """

    def __init__(self, monkeypatch):
        self.n = 0
        real = Image.open

        def counted(*a, **k):
            self.n += 1
            return real(*a, **k)
        monkeypatch.setattr(photo_pages.Image, "open", counted)


def a_photo(path: Path, stamp=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (60, 40), (7, 7, 7))
    if stamp:
        exif = img.getexif()
        exif[36867] = stamp                      # DateTimeOriginal
        img.save(path, format="JPEG", exif=exif)
    else:
        img.save(path, format="JPEG")


def a_job(tmp_path, *names, stamps=None):
    home = tmp_path / "jobs"
    job = home / JOB
    (job / "Photos").mkdir(parents=True)
    for i, name in enumerate(names):
        a_photo(job / "Photos" / name,
                stamp=(stamps or {}).get(name))
    return home, job


@pytest.fixture
def client(tmp_path, monkeypatch):
    home, job = a_job(tmp_path, *["IMG_%04d.jpeg" % i for i in range(8)])
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    return TestClient(create_app(), raise_server_exceptions=False), job


# --- it is read once --------------------------------------------------------

def test_the_first_read_opens_every_photograph(client, monkeypatch):
    c, job = client
    opens = Opens(monkeypatch)
    c.get("/api/jobs/%s/manifest" % JOB)
    assert opens.n == 8, "a cold job should read all eight, once"


def test_the_second_read_opens_nothing(client, monkeypatch):
    c, job = client
    c.get("/api/jobs/%s/manifest" % JOB)          # warm it
    opens = Opens(monkeypatch)
    c.get("/api/jobs/%s/manifest" % JOB)
    assert opens.n == 0, "it read the same photographs a second time"


def test_the_price_is_measured_once_and_then_remembered(client, monkeypatch):
    """Working out the price means decoding, resizing and re-encoding every
    photograph waiting for words. The screen asks for a fresh price after
    every click, so doing it once is the whole point."""
    c, job = client
    c.get("/api/jobs/%s/manifest" % JOB)

    first = Opens(monkeypatch)
    c.get("/api/jobs/%s/caption-estimate" % JOB)
    assert first.n == 8, "the first price should measure all eight, once"

    again = Opens(monkeypatch)
    c.get("/api/jobs/%s/caption-estimate" % JOB)
    assert again.n == 0, "it measured the same photographs a second time"


def test_a_click_opens_nothing(client, monkeypatch):
    """The measured fault: one tick of Mark Reviewed cost 130 file opens, and
    every tick is followed by a fresh price on top of it."""
    c, job = client
    m = c.get("/api/jobs/%s/manifest" % JOB).json()
    m["photos"][0]["caption"] = "A caption"
    c.put("/api/jobs/%s/manifest" % JOB, json=m)
    c.get("/api/jobs/%s/caption-estimate" % JOB)      # warm the price too

    opens = Opens(monkeypatch)
    c.post("/api/jobs/%s/photos/IMG_0000.jpeg/reviewed" % JOB)
    c.get("/api/jobs/%s/caption-estimate" % JOB)
    assert opens.n == 0, "a tick and a price still cost file opens"


def test_touching_one_photograph_re_reads_only_that_one(client, monkeypatch):
    c, job = client
    c.get("/api/jobs/%s/manifest" % JOB)          # warm it
    target = job / "Photos" / "IMG_0003.jpeg"
    target.touch()                                # its mtime moves

    opens = Opens(monkeypatch)
    capturedates.stamp_for(job)(target)
    assert opens.n == 1, "a changed photograph should cost exactly one read"


# --- and the order is identical ---------------------------------------------

def test_the_order_is_the_same_with_the_cache_as_without(tmp_path):
    """The whole point is speed. If it changes the order of a report's
    photographs it is worse than useless."""
    names = ["b.jpeg", "a.jpeg", "IMG_2.jpeg", "IMG_10.jpeg"]
    stamps = {"b.jpeg": "2024:01:01 09:00:00",
              "a.jpeg": "2024:01:01 08:00:00"}
    home, job = a_job(tmp_path, *names, stamps=stamps)
    paths = [job / "Photos" / n for n in names]

    plain = [p.name for p in photo_pages.exif_order(paths)]
    cached = [p.name for p in photo_pages.exif_order(
        paths, stamp_for=capturedates.stamp_for(job))]
    assert cached == plain


def test_a_photograph_with_no_capture_time_still_sorts_by_name(tmp_path):
    home, job = a_job(tmp_path, "IMG_10.jpeg", "IMG_2.jpeg")
    paths = [job / "Photos" / n for n in ("IMG_10.jpeg", "IMG_2.jpeg")]
    ordered = [p.name for p in photo_pages.exif_order(
        paths, stamp_for=capturedates.stamp_for(job))]
    assert ordered == ["IMG_2.jpeg", "IMG_10.jpeg"], "2 must come before 10"


def test_a_photograph_that_cannot_be_read_does_not_take_the_screen_down(tmp_path):
    home, job = a_job(tmp_path)
    broken = job / "Photos" / "broken.jpeg"
    broken.write_bytes(b"this is not an image")
    assert capturedates.stamp_for(job)(broken) == ""


# --- and it stays out of Mark's folders -------------------------------------

def test_the_cache_never_lands_inside_the_job(client):
    c, job = client
    c.get("/api/jobs/%s/manifest" % JOB)
    store = capturedates.store_for(job / "Photos")
    assert thumbcache.cache_root() in store.parents
    assert job not in store.parents
    assert not list((job / "Photos").glob("*.json"))


def test_a_cache_that_cannot_be_written_still_answers(client, monkeypatch, tmp_path):
    c, job = client
    import state

    def refuse(*_a, **_k):
        raise OSError("read only")
    monkeypatch.setattr(state, "write_text", refuse)
    r = c.get("/api/jobs/%s/manifest" % JOB)
    assert r.status_code == 200
    assert len(r.json()["photos"]) == 8

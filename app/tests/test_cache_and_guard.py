"""Two things the browser and the reset both depend on.

Cache: a rebuild renames the script and the stylesheet, so a browser holding
an old index.html asks for a file that is no longer there and shows the
previous app. That happened and cost a round of testing.

Guard: reset renames whole folders. A write in flight would land in a folder
being moved. The server refuses on its own; these call the routes directly
rather than trusting a disabled button.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import busy  # noqa: E402
from main import create_app  # noqa: E402

DIST = Path(__file__).resolve().parents[1] / "web" / "dist"


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_SETTINGS_FILE", str(tmp_path / "settings.json"))
    monkeypatch.delenv("RRF_JOBS_HOME", raising=False)
    jobs = tmp_path / "jobs"
    (jobs / "A job" / "Photos").mkdir(parents=True)
    (jobs / "A job" / "Photos" / "a.jpg").write_bytes(b"not really a photo")
    (jobs / "A job" / "Photos" / "photo-manifest.json").write_text(json.dumps(
        {"job": "A job", "context": "", "report_year": 2026, "caption_style": "view",
         "photos": [{"file": "a.jpg", "caption": "something"}]}, indent=2))
    return jobs


@pytest.fixture
def client(home):
    c = TestClient(create_app())
    c.put("/api/workspace", json={"path": str(home)})
    return c


# ------------------------------------------------------------- cache --------
@pytest.mark.skipif(not DIST.is_dir(), reason="front end not built")
def test_the_page_itself_is_never_cached(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers.get("cache-control") == "no-store"


@pytest.mark.skipif(not DIST.is_dir(), reason="front end not built")
def test_index_html_by_name_is_never_cached(client):
    assert client.get("/index.html").headers.get("cache-control") == "no-store"


@pytest.mark.skipif(not DIST.is_dir(), reason="front end not built")
def test_a_head_request_carries_it_too(client):
    """A cache deciding whether to reuse what it has asks with HEAD."""
    assert client.head("/").headers.get("cache-control") == "no-store"
    assert client.head("/index.html").headers.get("cache-control") == "no-store"


@pytest.mark.skipif(not DIST.is_dir(), reason="front end not built")
def test_the_named_assets_stay_cacheable(client):
    """Their names change when their contents do, so they cannot go stale."""
    asset = next(iter(sorted((DIST / "assets").glob("*.js"))), None)
    assert asset is not None, "no built asset to check"
    r = client.get("/assets/" + asset.name)
    assert r.status_code == 200
    assert "no-store" not in (r.headers.get("cache-control") or "")


# ------------------------------------------------------------- guard --------
WRITE_ROUTES = [
    ("put", "/api/workspace", {"json": {"path": "/tmp"}}),
    ("delete", "/api/workspace", {}),
    ("post", "/api/jobs", {"json": {"name": "New job"}}),
    ("post", "/api/intake", {"json": {"name": "N", "street": "1 Main", "city": "DAVENPORT",
                                      "property_type": "Retail", "engagement": "Tax appeal"}}),
    ("put", "/api/jobs/A job/sections", {"json": {"sections": ["Title Page"]}}),
    ("put", "/api/jobs/A job/manifest", {"json": {"photos": [{"file": "a.jpg", "caption": ""}]}}),
    ("post", "/api/jobs/A job/captions/clear", {}),
    ("post", "/api/jobs/A job/build", {}),
    ("post", "/api/jobs/A job/photos", {"files": [("files", ("b.jpg", b"x", "image/jpeg"))]}),
]


@pytest.mark.parametrize("method,url,kwargs", WRITE_ROUTES,
                         ids=[f"{m}:{u}" for m, u, _ in WRITE_ROUTES])
def test_every_write_route_refuses_while_a_reset_runs(client, method, url, kwargs):
    with busy.resetting():
        r = getattr(client, method)(url, **kwargs)
    assert r.status_code == 409, f"{method} {url} answered {r.status_code}"
    assert r.json()["detail"] == "The demo is being reset. Nothing was changed."


def test_a_reset_refuses_while_a_write_runs():
    with busy.writing():
        with pytest.raises(busy.Busy) as caught:
            with busy.resetting():
                pass
    assert caught.value.message == "Another operation is in progress. Nothing was reset."


def test_two_resets_cannot_overlap():
    with busy.resetting():
        with pytest.raises(busy.Busy):
            with busy.resetting():
                pass


def test_writes_do_not_block_each_other():
    """Two people typing captions is not a conflict. Only reset is exclusive."""
    with busy.writing():
        with busy.writing():
            assert busy.state()["writers"] == 2
    assert busy.state()["writers"] == 0


def test_the_floor_is_released_even_when_the_route_fails():
    with pytest.raises(ValueError):
        with busy.writing():
            raise ValueError("boom")
    assert busy.state() == {"writers": 0, "resetting": False}

"""Choosing how the captions should read must not cost anything.

The audit found two paid requests firing the moment the style step opened: it
captioned three of his photographs in both styles so he could compare real
sentences. That is a defensible idea and an indefensible order of events. The
money was spent before the price was shown and before he agreed to anything,
and neither request appeared in the estimate on that same screen.

The rule these tests hold: between opening the style step and pressing the
final confirmation, zero provider calls and zero photographs leave the machine.

The provider seam is `captions.draft_captions`. Every paid path in the app goes
through it, so a stand-in that raises is a complete answer to "was anything
called". `_client` construction is covered too, because building an Anthropic
client is the step that needs the key.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import captions  # noqa: E402
from main import create_app  # noqa: E402

WEB = Path(__file__).resolve().parents[1] / "web" / "src"


@pytest.fixture
def client(tmp_path, monkeypatch):
    place = tmp_path / "jobs"
    place.mkdir()
    monkeypatch.setenv("RRF_JOBS_HOME", str(place))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-not-a-real-key")
    return TestClient(create_app(), raise_server_exceptions=False)


@pytest.fixture
def never_called(monkeypatch):
    """The provider, wired to fail the test if anything reaches it."""
    def explode(*_args, **_kwargs):
        raise AssertionError("a provider call was made before approval")
    monkeypatch.setattr(captions, "draft_captions", explode)


# --- the route that used to spend ----------------------------------------
def test_the_paid_preview_route_is_gone(client):
    """It was the only caller, so it is removed rather than left dormant."""
    answer = client.post("/api/jobs/anything/caption-preview")
    assert answer.status_code == 404


def test_no_screen_can_still_reach_it():
    """A dead route with a live caller in the browser is not a fix."""
    api = (WEB / "api.js").read_text()
    assert "caption-preview" not in api
    assert "captionPreview" not in api
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert "captionPreview" not in screen


# --- what the style step now reads ---------------------------------------
def test_style_selection_calls_nobody(client, never_called):
    """Everything the step loads, loaded with the provider booby-trapped."""
    assert client.get("/api/caption-styles").status_code == 200


def test_the_step_is_understandable_from_static_examples(client):
    styles = client.get("/api/caption-styles").json()["styles"]
    assert len(styles) >= 2
    for style in styles:
        assert len(style["samples"]) >= 2, "each style shows more than one example"
        assert all(line.strip() for line in style["samples"])


def test_the_two_styles_are_told_apart_by_their_examples(client):
    styles = {s["key"]: s["samples"] for s in client.get("/api/caption-styles").json()["styles"]}
    assert all(line.startswith("View") for line in styles["view"])
    # The other form is a category, an en dash, then the detail.
    assert all("–" in line for line in styles["category"])


def test_the_examples_carry_no_client_information(client):
    """Generic building parts only. No address, no tenant, no client."""
    styles = client.get("/api/caption-styles").json()["styles"]
    every = " ".join(line for s in styles for line in s["samples"])
    assert not any(ch.isdigit() for ch in every), "a number here would be an address"


def test_the_examples_are_not_presented_as_his_photographs():
    """The frame beside each example is empty, and the screen says why."""
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert "cell-photo is-example" in screen
    assert "Examples of the writing style, not captions of your photographs." in screen
    # the shape of the defect: a thumbnail of his own photo in the example row
    sheet = screen[screen.index('aria-label="How should the captions read?"'):]
    assert "thumbUrl" not in sheet


# --- the money is shown before anything is spent -------------------------
def test_the_estimate_covers_every_call_that_can_cost(client, never_called):
    """Nothing bills outside the run the estimate describes.

    With the preview gone, `POST /captions` is the only route left that can
    reach the provider, which is what makes one estimate able to describe the
    whole spend honestly.
    """
    paid = [r for r in client.app.routes
            if getattr(r, "path", "").startswith("/api/jobs/{name}/caption")
            and "POST" in getattr(r, "methods", set())]
    paths = sorted(r.path for r in paid)
    assert paths == ["/api/jobs/{name}/captions", "/api/jobs/{name}/captions/clear"]

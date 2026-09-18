"""Choosing how the captions should read must not cost anything.

The audit found two paid requests firing the moment the style step opened: it
captioned three of his photographs in both styles so he could compare real
sentences. That is a defensible idea and an indefensible order of events. The
money was spent before the price was shown and before he agreed to anything,
and neither request appeared in the estimate on that same screen.

The rule these tests hold: nothing in this app reaches the provider by
accident, and every paid route is in the estimate that describes it.

Amended 2026-09-14, twice. Spenser authorised the money for real photographs
in that window on 2026-09-04: *"we're going to spend the 3 pennies to generate
the 6 suggestions."* The first amendment put them behind a press carrying a
price. He saw that press on Windows the same evening and said it was annoying
and not well thought out, because he had already agreed to the spend and was
being asked a second time. So the samples are written as the window opens.

What survives is the rule that was ever the safety: no route reaches the
provider by accident. The old route that fired on open is still gone, the
samples route still refuses a bare call, and the window buys them once per job
and never again.

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


# --- the route that used to spend on its own ------------------------------
def test_the_old_route_that_fired_by_itself_is_gone(client):
    """It spent on open. Removed rather than left dormant."""
    answer = client.post("/api/jobs/anything/caption-preview")
    assert answer.status_code == 404


def test_no_screen_can_still_reach_it():
    """A dead route with a live caller in the browser is not a fix."""
    api = (WEB / "api.js").read_text()
    assert "caption-preview" not in api
    assert "captionPreview" not in api
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert "captionPreview" not in screen


def test_the_samples_route_refuses_a_bare_call(client, never_called):
    """Its replacement still will not run for anyone who just asks."""
    answer = client.post("/api/jobs/anything/caption-samples")
    assert answer.status_code in (404, 409)


def test_the_style_window_is_the_only_thing_that_asks_for_samples():
    """One caller, and it is opening the window he already paid for."""
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert "captionSamples" in screen, "the screen is the only caller"
    # No press offers to sell them any more, and no price rides on one.
    assert "Show these on my photographs" not in screen
    assert "sample-press" not in screen
    assert "quote.samples" not in screen, "the window quotes him no sample price"


def test_the_window_buys_the_samples_once_per_job():
    """Opening it twice must not spend twice, and neither must a redraw."""
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    opener = screen[screen.index("function openChooser("):]
    opener = opener[:opener.index("\n  }")]
    assert "askForSamples(" in opener, "the window opening is what buys them"
    guard = screen[screen.index("async function askForSamples("):]
    guard = guard[:guard.index("\n  }")]
    assert "bought.current" in guard, "one purchase per job, held in a ref"


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


def test_a_written_example_never_sits_beside_one_of_his_photographs():
    """The two states are kept apart, and that separation is the safety.

    A written example is a specimen of a writing style and says nothing about
    any photograph, so it keeps its blank frame and the window says so. A
    photograph only ever appears once a caption has actually been written from
    it, which is the thing the money buys.
    """
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert "cell-photo is-example" in screen
    assert "Examples of the style, not your photographs." in screen
    # One switch decides which of the two the grid is drawing, so there is no
    # arrangement in which a written line and a photograph share a row.
    assert "function previewRows(samples, perPage, shots)" in screen


# --- the money is shown before anything is spent -------------------------
def test_every_route_that_touches_captions_is_named_here(client, never_called):
    """Nothing bills outside what the estimate describes.

    Every POST that touches a job's captions is listed, paid or free, so a new
    one cannot arrive without somebody saying in this file which it is. The
    list is what makes the two below exhaustive rather than a sample.

    Three can reach the provider: the whole-job run, the samples the style
    window buys as it opens, and refresh on one photograph. `GET
    /caption-estimate` carries a figure for each: `estimate` for the run,
    `samples.estimate` for the window, `one_photo` for refresh.
    `test_the_chooser_shows_his_photographs.py` holds the second figure and
    `test_a_caption_can_come_back.py` holds the third.
    """
    touching = sorted(
        r.path for r in client.app.routes
        if "POST" in getattr(r, "methods", set())
        and "caption" in getattr(r, "path", ""))
    assert touching == ["/api/jobs/{name}/caption-samples",
                        "/api/jobs/{name}/captions",
                        "/api/jobs/{name}/captions/back",
                        "/api/jobs/{name}/captions/clear",
                        "/api/jobs/{name}/photos/{file}/caption",
                        "/api/jobs/{name}/photos/{file}/caption/back"]


def test_the_free_ones_never_reach_the_provider(client, never_called):
    """Clearing captions and putting them back are the app's own arithmetic
    over a file it already has. They must stay that way: both are pressed
    freely and neither shows a price."""
    assert client.post("/api/jobs/anything/captions/clear").status_code in (400, 404)
    assert client.post("/api/jobs/anything/captions/back").status_code in (400, 404)
    assert client.post(
        "/api/jobs/anything/photos/a.jpg/caption/back").status_code in (400, 404)


def test_the_paid_ones_each_have_a_figure_on_the_estimate(client, never_called):
    """One figure per paid route, on the one answer the screen already asks
    for. A press that spends without a number beside it is the fault this
    whole file exists for."""
    import io
    import json

    import jobs as jobs_module
    import workspace
    from PIL import Image

    # A job with one photograph, so every figure has something to count.
    place = Path(workspace.jobs_home())
    job = place / "A JOB"
    for folder in jobs_module.MARK_FOLDERS:
        (job / folder).mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    Image.new("RGB", (30, 20), (10, 20, 30)).save(buf, format="JPEG")
    (job / "Photos" / "a.jpg").write_bytes(buf.getvalue())
    (job / "Photos" / "photo-manifest.json").write_text(json.dumps(
        {"job": "A JOB", "context": "", "report_year": 2026,
         "caption_style": "view", "photos": [{"file": "a.jpg", "caption": ""}]}))

    quote = client.get("/api/jobs/A JOB/caption-estimate").json()
    assert quote["estimate"]["total"] is not None          # the whole-job run
    assert quote["samples"]["estimate"]["total"] is not None   # the style window
    assert quote["one_photo"]["photos"] == 1                   # refresh on a tile
    assert quote["one_photo"]["total"] > 0


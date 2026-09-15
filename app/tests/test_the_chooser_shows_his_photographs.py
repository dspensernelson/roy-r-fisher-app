"""Real photographs in the caption style chooser, paid for on purpose.

Spenser, 2026-09-04: *"There need to be real photos in here... we're going to
spend the 3 pennies to generate the 6 suggestions. It should be the first 3
photos."* He authorised the money. `docs/THE-WALK-2026-09-04.md`, click 8.

The window writes them as it opens. That is the whole of the authorisation he
gave: three photographs, both styles, once per job. It sat behind a press for
one evening and he threw the press out on 2026-09-14: *"its annoying and not
well thought out"*. He had already agreed to the spend.

What `test_no_spend_before_approval.py` guards is unchanged. The route still
refuses a bare call, the screen still buys once per job, and nothing else in
the app can reach the provider by accident.

Everything here runs with a stand-in for the model, so the file costs nothing.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import aipolicy  # noqa: E402
import captions  # noqa: E402
import usage as usage_store  # noqa: E402
from main import create_app  # noqa: E402

JOB = "ANYTOWN_100 Example Avenue - 2026"
USED = {"input": 20000, "output": 400, "cache_write": 0, "cache_read": 0}


def make_job(home: Path, photos: int = 8, name: str = JOB) -> Path:
    job = home / name
    (job / "Photos").mkdir(parents=True)
    for i in range(photos):
        Image.new("RGB", (800, 600), (40 + i, 90, 120)).save(
            job / "Photos" / ("p%02d.jpg" % i))
    return job


@pytest.fixture
def home(tmp_path, monkeypatch):
    place = tmp_path / "jobs"
    place.mkdir()
    monkeypatch.setenv("RRF_JOBS_HOME", str(place))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-not-a-real-key")
    return place


@pytest.fixture
def client(home):
    make_job(home)
    return TestClient(create_app(), raise_server_exceptions=False)


@pytest.fixture
def model(monkeypatch):
    """A model that writes captions and never touches the network."""
    calls = {"requests": 0, "sent": [], "styles": []}

    def fake(context, paths, style=None):
        calls["requests"] += 1
        calls["sent"].append([p.name for p in paths])
        calls["styles"].append(style)
        return ({p.name: "%s %s" % (style, p.stem) for p in paths}, dict(USED))

    monkeypatch.setattr(captions, "draft_captions", fake)
    return calls


@pytest.fixture
def never_called(monkeypatch):
    def explode(*_args, **_kwargs):
        raise AssertionError("a provider call was made before the press")
    monkeypatch.setattr(captions, "draft_captions", explode)


def samples(client, confirmed=True, job=JOB):
    url = "/api/jobs/%s/caption-samples" % job
    if confirmed:
        url += "?confirmed=true"
    return client.post(url)


def manifest_of(client, job=JOB):
    return client.get("/api/jobs/%s/manifest" % job).json()


# --- everything else the window loads is still free ------------------------

def test_the_styles_and_the_price_call_nobody(client, never_called):
    """The samples are the only paid thing the window touches."""
    assert client.get("/api/caption-styles").status_code == 200
    assert client.get("/api/jobs/%s/caption-estimate" % JOB).status_code == 200


def test_the_samples_will_not_run_for_a_bare_call(client, never_called):
    """A deliberate caller only. Nothing wanders into this route."""
    answer = samples(client, confirmed=False)
    assert answer.status_code == 409
    assert "confirm" in answer.json()["detail"].lower()


# --- what opening the window buys -----------------------------------------

def test_it_captions_the_first_three_photographs_in_both_styles(client, model):
    body = samples(client).json()
    assert body["ai_available"] is True
    assert [p["file"] for p in body["photos"]] == ["p00.jpg", "p01.jpg", "p02.jpg"]

    assert set(body["samples"]) == set(captions.STYLES)
    for key in captions.STYLES:
        lines = body["samples"][key]
        assert [line["file"] for line in lines] == ["p00.jpg", "p01.jpg", "p02.jpg"]
        assert all(line["caption"].strip() for line in lines)

    # Two styles, three photographs each. Six captions, two requests.
    assert model["requests"] == 2
    assert sorted(model["styles"]) == sorted(captions.STYLES)
    assert model["sent"] == [["p00.jpg", "p01.jpg", "p02.jpg"]] * 2


def test_the_samples_are_never_written_into_the_job(client, model):
    before = manifest_of(client)
    samples(client)
    after = manifest_of(client)
    assert [p.get("caption", "") for p in after["photos"]] == \
           [p.get("caption", "") for p in before["photos"]]
    assert all(not (p.get("caption") or "").strip() for p in after["photos"])


def test_a_caption_he_has_typed_is_never_resent(client, model):
    """His own words are not sent to the model and not paid for again."""
    live = manifest_of(client)
    live["photos"][0]["caption"] = "View of the loading dock he typed himself"
    assert client.put("/api/jobs/%s/manifest" % JOB, json=live).status_code == 200

    body = samples(client).json()
    assert [p["file"] for p in body["photos"]] == ["p01.jpg", "p02.jpg", "p03.jpg"]
    assert all("p00.jpg" not in batch for batch in model["sent"])
    assert manifest_of(client)["photos"][0]["caption"] == \
           "View of the loading dock he typed himself"


def test_what_it_spent_is_recorded_where_he_can_see_it(client, model):
    body = samples(client).json()
    assert body["measured"]["calculated_cost"] is not None
    runs = usage_store.runs()
    assert len(runs) == 1
    assert runs[0]["photos_requested"] == 6


# --- the fallbacks, because the window must still work ---------------------

def test_no_key_on_the_machine_means_written_examples(client, monkeypatch, never_called):
    monkeypatch.setattr(captions, "ai_available", lambda: False)
    body = samples(client).json()
    assert body["ai_available"] is False
    assert body["samples"] == {}


def test_a_demo_job_is_refused_before_a_client_is_built(client, monkeypatch, never_called):
    monkeypatch.setattr(aipolicy, "classify_job", lambda _job: aipolicy.LOCAL_ONLY)
    answer = samples(client)
    assert answer.status_code == 403


def test_a_job_with_every_caption_written_asks_for_nothing(client, model):
    live = manifest_of(client)
    for entry in live["photos"]:
        entry["caption"] = "View of something he already wrote"
    client.put("/api/jobs/%s/manifest" % JOB, json=live)
    body = samples(client).json()
    assert body["samples"] == {}
    assert model["requests"] == 0


# --- the samples are still counted, because he is still paying -------------

def test_the_estimate_still_accounts_for_the_samples(client):
    quote = client.get("/api/jobs/%s/caption-estimate" % JOB).json()
    shown = quote["samples"]
    # Three photographs, both styles, so six photographs are paid for.
    assert shown["photos"] == 3
    assert shown["styles"] == 2
    assert shown["estimate"]["photos"] == 6
    assert shown["estimate"]["total"] == 0.30


# --- the shape of the page it claims to be showing -------------------------

def test_the_preview_columns_match_the_printed_page():
    """The window says it draws the printed page, so it has to draw its shape.

    Spenser, 2026-09-14: *"one short caption floats alone in a large white
    field"*. He was looking at a real defect. The preview gave the photograph
    230 pixels and the caption everything else, while the printed page gives
    the photograph four inches of a 6.70 inch table and the caption what is
    left. The proportions were the wrong way round.

    The ratio cannot be imported into a stylesheet, so it is checked here
    against the engine's own number rather than trusted to stay in step.
    """
    import re
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
    import photo_pages

    css = (Path(__file__).resolve().parents[1] / "web" / "src" / "brand.css").read_text()
    block = css[css.index(".page-preview {"):]
    block = block[:block.index("}")]
    found = re.search(r"grid-template-columns:\s*([\d.]+)fr\s+([\d.]+)fr", block)
    assert found, "the two columns are in the engine's proportion, not in pixels"
    photo, caption = float(found.group(1)), float(found.group(2))
    assert photo == photo_pages.THREE_UP.width_in
    assert caption < photo, "the photograph is the wider half on the printed page"

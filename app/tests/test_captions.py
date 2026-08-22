import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
from main import create_app  # noqa: E402
import captions  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / "jobs"
    (home / "JOB1" / "Photos").mkdir(parents=True)
    Image.new("RGB", (300, 200), (120, 32, 40)).save(home / "JOB1" / "Photos" / "a.jpg")
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    c = TestClient(create_app())
    m = c.get("/api/jobs/JOB1/manifest").json()
    m["photos"] = [{"file": "a.jpg", "caption": ""}]
    c.put("/api/jobs/JOB1/manifest", json=m)
    return c


def test_the_two_styles_are_the_two_the_corpus_actually_shows():
    assert set(captions.STYLES) == {"view", "category"}
    view = captions.STYLES["view"]
    category = captions.STYLES["category"]
    # Measured 2026-08-10: four delivered photo documents carry 79 "View of"
    # captions; one carries 24 in the category-and-dash form.
    assert view["thin_evidence"] is False
    assert category["thin_evidence"] is True
    assert captions.DEFAULT_STYLE == "view"


def test_each_style_teaches_only_its_own_examples():
    view = captions.system_prompt("view")
    category = captions.system_prompt("category")
    assert "View of northwest corner facing southeast" in view
    assert "Building exterior" not in view          # the other report's shape
    assert "Common Area" in category
    assert "View of northwest corner" not in category


def test_neither_style_may_invent_a_compass_direction():
    """A photograph does not show which way the camera pointed. The first live
    run guessed 'facing east' and 'facing north' on a Walmart, and called
    Mark's retention pond green space. A wrong direction in a delivered report
    is worse than a blank one, so both styles must forbid guessing it."""
    for style in captions.STYLES:
        prompt = captions.system_prompt(style).lower()
        assert "compass direction" in prompt
        assert "do not guess" in prompt or "never state one unless" in prompt


def test_unknown_style_falls_back_rather_than_raising():
    assert captions.system_prompt("nonsense") == captions.system_prompt(captions.DEFAULT_STYLE)


def test_property_type_picks_the_starting_style():
    assert captions.default_style("multi-family") == "category"
    assert captions.default_style("Multi-Family (LIHTC)") == "category"
    assert captions.default_style("retail") == "view"
    assert captions.default_style("office") == "view"
    assert captions.default_style("industrial") == "view"
    assert captions.default_style("") == "view"


def test_a_new_manifest_starts_on_the_style_the_property_type_suggests(tmp_path, monkeypatch):
    import brief
    import photos as photos_mod
    job = tmp_path / "APARTMENTS"
    (job / "Photos").mkdir(parents=True)
    brief.write_brief(job, {"Property address": "1 Main St", "Property type": "multi-family"}, [])
    assert photos_mod.load_manifest(job)["caption_style"] == "category"

    shop = tmp_path / "SHOP"
    (shop / "Photos").mkdir(parents=True)
    brief.write_brief(shop, {"Property address": "2 Main St", "Property type": "retail"}, [])
    assert photos_mod.load_manifest(shop)["caption_style"] == "view"


def test_marks_own_pick_survives_a_reload(tmp_path):
    """His choice outranks the property type, and nothing re-guesses it later."""
    import brief
    import photos as photos_mod
    job = tmp_path / "APARTMENTS"
    (job / "Photos").mkdir(parents=True)
    brief.write_brief(job, {"Property type": "multi-family"}, [])
    manifest = photos_mod.load_manifest(job)
    manifest["caption_style"] = "view"                 # Mark overrides the suggestion
    photos_mod.save_manifest(job, manifest)
    assert photos_mod.load_manifest(job)["caption_style"] == "view"


def test_drafting_uses_the_style_recorded_on_the_job(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    manifest = client.get("/api/jobs/JOB1/manifest").json()
    manifest["caption_style"] = "category"
    client.put("/api/jobs/JOB1/manifest", json=manifest)

    seen = {}

    def spy(context, paths, style=captions.DEFAULT_STYLE):
        seen["style"] = style
        return {"a.jpg": "Common Area - front entry"}, {"input": 100, "output": 20}

    with patch.object(captions, "draft_captions", spy):
        client.post("/api/jobs/JOB1/captions")
    assert seen["style"] == "category"


def test_the_screen_can_ask_what_the_two_styles_look_like(client):
    """One source for the styles: the screen reads them rather than
    restating them, so the samples on screen cannot drift from the prompt."""
    body = client.get("/api/caption-styles").json()
    keys = [s["key"] for s in body["styles"]]
    assert keys == ["view", "category"]             # house default first
    for style in body["styles"]:
        assert style["label"] and style["sample"] and style["note"]
    category = [s for s in body["styles"] if s["key"] == "category"][0]
    assert category["thin_evidence"] is True
    assert "one delivered report" in category["note"].lower()


def test_missing_key_degrades_gracefully(client):
    r = client.post("/api/jobs/JOB1/captions")
    assert r.status_code == 200
    body = r.json()
    assert body["ai_available"] is False
    assert body["photos"][0]["caption"] == ""


def test_captions_fill_only_blank_ones(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with patch.object(captions, "draft_captions", return_value=({"a.jpg": "View of front entrance"}, {"input": 100, "output": 20})):
        body = client.post("/api/jobs/JOB1/captions").json()
    assert body["ai_available"] is True
    assert body["photos"][0]["caption"] == "View of front entrance"
    # Mark's edit wins: re-run must not touch a non-empty caption
    with patch.object(captions, "draft_captions", return_value=({"a.jpg": "SOMETHING ELSE"}, {"input": 100, "output": 20})):
        body2 = client.post("/api/jobs/JOB1/captions").json()
    assert body2["photos"][0]["caption"] == "View of front entrance"

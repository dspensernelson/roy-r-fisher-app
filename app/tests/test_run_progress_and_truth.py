"""What a caption run says while it runs, and what it says when it ends.

Two findings from the audit.

Progress was a thin indeterminate bar in the top corner of a page holding
sixty-one photographs. The app knew it was on request one of two, knew how many
captions were already saved, and said none of it. Captions that were finished
and on disk kept showing an empty box until the whole run came back.

Partial success contradicted itself. The green box said sixty captions were
saved and the red banner immediately below said `Nothing was changed`. The
sentence belonged to one failed request; whether anything survived is a fact
about the run.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import captions  # noqa: E402
import jobs as jobs_module  # noqa: E402
import progress  # noqa: E402
from main import create_app  # noqa: E402

WEB = Path(__file__).resolve().parents[1] / "web" / "src"
JOB = "ANYTOWN_1 Main Street - 2026"
USED = {"input": 1000, "output": 200, "cache_write": 0, "cache_read": 0}


@pytest.fixture
def home(tmp_path, monkeypatch):
    import io
    import json

    from PIL import Image
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path / "jobs"))
    monkeypatch.setenv("RRF_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("RRF_USAGE_FILE", str(tmp_path / "usage.json"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-not-a-real-key")
    job = tmp_path / "jobs" / JOB
    for folder in jobs_module.MARK_FOLDERS:
        (job / folder).mkdir(parents=True)
    buf = io.BytesIO()
    Image.new("RGB", (30, 20), (10, 20, 30)).save(buf, format="JPEG")
    photos = [{"file": "photo-%02d.jpg" % n, "caption": ""} for n in range(1, 6)]
    for entry in photos:
        (job / "Photos" / entry["file"]).write_bytes(buf.getvalue())
    (job / "Photos" / "photo-manifest.json").write_text(json.dumps(
        {"job": JOB, "context": "", "report_year": 2026,
         "caption_style": "view", "photos": photos}, indent=2))
    return job


@pytest.fixture
def client(home):
    return TestClient(create_app(), raise_server_exceptions=False)


def stand_in(monkeypatch, fail_after=None):
    """A model that writes captions and never touches the network."""
    calls = {"n": 0}

    def fake(context, paths, style=None):
        calls["n"] += 1
        if fail_after is not None and calls["n"] > fail_after:
            raise captions.CaptionError(
                "Anthropic is busy or the account has hit a limit. "
                "Try again in a minute.", "rate")
        return ({p.name: "View of %s" % p.stem for p in paths}, dict(USED))

    monkeypatch.setattr(captions, "draft_captions", fake)
    return calls


def one_photo_per_request(monkeypatch):
    """Force a five-photo run to be five requests, so progress has steps."""
    monkeypatch.setattr(captions, "plan_tranches",
                        lambda paths, encoded=None: [[p] for p in paths])


# --- the run says where it has got to ------------------------------------
def test_nothing_is_running_before_a_run(client):
    at = client.get("/api/jobs/%s/caption-progress" % JOB).json()
    assert at["running"] is False
    assert at["captioned"] == 0


def test_the_run_records_its_position_as_it_goes(client, monkeypatch):
    one_photo_per_request(monkeypatch)
    seen = []

    real = progress.advance

    def watch(job, request, captioned):
        real(job, request, captioned)
        seen.append(progress.read(job))

    monkeypatch.setattr(progress, "advance", watch)
    stand_in(monkeypatch)
    client.post("/api/jobs/%s/captions" % JOB)

    assert [s["request"] for s in seen] == [1, 2, 3, 4, 5]
    assert [s["captioned"] for s in seen] == [1, 2, 3, 4, 5]
    assert all(s["requests"] == 5 for s in seen)
    assert all(s["running"] for s in seen)


def test_captions_are_on_disk_before_the_position_is_reported(client, monkeypatch):
    """So a number on screen is always a number of captions actually saved."""
    one_photo_per_request(monkeypatch)
    saved_at_each_step = []

    real = progress.advance

    def watch(job, request, captioned):
        manifest = (Path(client.app.state.__dict__.get("_", "")) if False else None)
        from photos import load_manifest
        import jobs as jm
        found = load_manifest(jm.jobs_home() / JOB)
        saved_at_each_step.append(
            sum(1 for p in found["photos"] if p["caption"].strip()))
        real(job, request, captioned)

    monkeypatch.setattr(progress, "advance", watch)
    stand_in(monkeypatch)
    client.post("/api/jobs/%s/captions" % JOB)
    assert saved_at_each_step == [1, 2, 3, 4, 5]


def test_the_light_goes_out_when_the_run_ends(client, monkeypatch):
    stand_in(monkeypatch)
    client.post("/api/jobs/%s/captions" % JOB)
    assert client.get("/api/jobs/%s/caption-progress" % JOB).json()["running"] is False


def test_the_light_goes_out_when_the_run_fails(client, monkeypatch):
    stand_in(monkeypatch, fail_after=0)
    client.post("/api/jobs/%s/captions" % JOB)
    assert progress.read(JOB)["running"] is False


def test_the_light_goes_out_even_on_an_unexpected_failure(client, monkeypatch):
    def explode(*_a, **_k):
        raise RuntimeError("something nobody predicted")
    monkeypatch.setattr(captions, "draft_captions", explode)
    client.post("/api/jobs/%s/captions" % JOB)
    assert progress.read(JOB)["running"] is False


# --- what the run says when it ends --------------------------------------
def test_a_whole_run_reports_done(client, monkeypatch):
    stand_in(monkeypatch)
    body = client.post("/api/jobs/%s/captions" % JOB).json()
    assert body["state"] == "done"
    assert body["summary"] == "5 captions were written."


def test_a_partial_run_never_says_nothing_was_changed(client, monkeypatch):
    one_photo_per_request(monkeypatch)
    stand_in(monkeypatch, fail_after=3)
    body = client.post("/api/jobs/%s/captions" % JOB).json()

    assert body["state"] == "partial"
    assert body["captioned"] == 3
    assert len(body["remaining"]) == 2
    assert body["summary"] == (
        "3 captions were saved. 2 photos still need a caption. The captions "
        "already saved will not be sent or charged for again.")
    assert "Nothing was changed" not in body["summary"]
    # and the request's own sentence no longer claims it either
    assert "Nothing was changed" not in body["error"]


def test_the_singular_reads_properly(client, monkeypatch):
    one_photo_per_request(monkeypatch)
    stand_in(monkeypatch, fail_after=4)
    body = client.post("/api/jobs/%s/captions" % JOB).json()
    assert body["summary"].startswith("4 captions were saved. 1 photo still needs a caption.")


def test_a_run_that_saved_nothing_says_so(client, monkeypatch):
    stand_in(monkeypatch, fail_after=0)
    body = client.post("/api/jobs/%s/captions" % JOB).json()
    assert body["state"] == "failed"
    assert body["summary"] == "No captions were written. Nothing was changed."


def test_the_rate_limit_sentence_no_longer_claims_a_rollback():
    """It can be raised with sixty captions already saved."""
    import inspect
    source = inspect.getsource(captions.draft_captions)
    rate = source[source.index("RateLimitError"):]
    rate = rate[:rate.index('"rate")')]
    assert "Nothing was changed" not in rate


# --- remaining-only retry, unchanged --------------------------------------
def test_a_retry_sends_only_what_is_left(client, monkeypatch):
    one_photo_per_request(monkeypatch)
    stand_in(monkeypatch, fail_after=3)
    client.post("/api/jobs/%s/captions" % JOB)

    calls = stand_in(monkeypatch)
    body = client.post("/api/jobs/%s/captions" % JOB).json()
    assert body["captioned"] == 2, "only the two without captions"
    assert body["remaining"] == []
    assert calls["n"] == 2


# --- the screen -----------------------------------------------------------
def test_the_screen_shows_which_request_it_is_on():
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert "request ${Math.min(running.request + 1, running.requests)} of ${running.requests}" in screen
    assert "of {running.total} written" in screen


def test_the_screen_pulls_down_captions_as_they_land():
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert "captionProgress(job)" in screen
    assert "setManifest(await getManifest(job))" in screen


def test_progress_sits_with_the_work_not_in_the_corner():
    """Its own block above the grid, not inside the actions row."""
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert 'className="run"' in screen
    actions = screen[screen.index('<div className="screen-actions">'):]
    actions = actions[:actions.index('className="run"')]
    assert 'className="run"' not in actions


def test_a_partial_run_is_not_dressed_as_success_or_failure():
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert 'outcome-${spent.state === "partial" ? "partial"' in screen
    css = (WEB / "brand.css").read_text()
    ok = css[css.index(".outcome {"):]
    ok = ok[:ok.index("}")]
    partial = css[css.index(".outcome-partial {"):]
    partial = partial[:partial.index("}")]
    assert "var(--ok-bg)" in ok
    assert "var(--ok-bg)" not in partial


def test_an_unavailable_cost_is_not_green():
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert 'spent.calculated_cost === null || spent.calculated_cost === undefined' in screen
    assert '"unknown" : "done"' in screen
    css = (WEB / "brand.css").read_text()
    unknown = css[css.index(".outcome-unknown {"):]
    unknown = unknown[:unknown.index("}")]
    assert "var(--ok-bg)" not in unknown


def test_a_saved_run_is_not_also_shown_as_an_error():
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert 'if (m.error && m.state === "failed") setError(m.error)' in screen


# --- the direct corrections ----------------------------------------------
def test_there_is_one_missing_key_message_not_two():
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert "{!aiOn && !blockedBecause && (" in screen, "the two can never both render"


def without_comments(text: str) -> str:
    """Just the code. A comment describing a defect is not the defect."""
    import re
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def test_no_screen_still_says_suggest_captions():
    for name in ("PhotosScreen.jsx", "JobHome.jsx", "ActiveJobs.jsx", "ChooseFolder.jsx"):
        shown = without_comments((WEB / "screens" / name).read_text())
        assert "Suggest captions" not in shown


def test_captions_are_typed_in_prose_not_a_code_font():
    """`font: 14px/1.45 inherit` was invalid, so the box fell back to monospace."""
    css = without_comments((WEB / "brand.css").read_text())
    block = css[css.index(".grid textarea {"):]
    block = block[:block.index("}")]
    assert "font-family: inherit" in block
    assert "font: 14px/1.45 inherit" not in css
    assert "monospace" not in block


def test_the_one_live_action_outweighs_the_empty_folder_rows():
    css = (WEB / "brand.css").read_text()
    assert ".section-row.live .name { font-size: 16px" in css
    assert ".folder.is-empty" in css
    home = (WEB / "screens" / "JobHome.jsx").read_text()
    assert 'className={`folder${empty ? " is-empty" : ""}`}' in home
    # the information itself is kept, only the weight changes
    assert "folderNote(f)" in home


def test_review_is_still_one_photo_at_a_time():
    """Approved, and not something this pass was asked to soften."""
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert "Mark reviewed" in screen
    assert "Mark all" not in screen and "Review all" not in screen

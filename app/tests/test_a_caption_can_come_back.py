"""Clearing captions is no longer the end of them.

Three controls, all approved by Spenser on 2026-09-17 from a drawing called
`one-photograph.html`, which is not in this repository yet:

* Back, on one photograph, which works on its own.
* Refresh, on one photograph, which is one model call.
* A job-wide back in the widget's bar, which **spares what he changed**.

The sparing rule is the one that needs proving hardest, because it is what
makes the job-wide back safe to press twice: a caption he typed after the
clear, or had written again after it, is not put back over.

Everything here runs against real folders and real manifest files on disk,
because these are judged by what they leave behind. Nothing here reaches the
network: the model is stood in for, which is one of the three conditions
`HOW-WE-WORK.md` allows to be stood in for.
"""
import io
import json
import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import captions  # noqa: E402
import jobs as jobs_module  # noqa: E402
import photos as photos_routes  # noqa: E402
from main import create_app  # noqa: E402

JOB = "DAVENPORT_2840 Brady Street - 2026 Tax"
USED = {"input": 1000, "output": 200, "cache_write": 0, "cache_read": 0}

WRITTEN = [
    {"file": "a.jpg", "caption": "View east from Brady Street", "reviewed": True},
    {"file": "b.jpg", "caption": "Rear loading area"},
    {"file": "c.jpg", "caption": ""},
]


def jpg_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (30, 20), (10, 20, 30)).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path / "jobs"))
    monkeypatch.setenv("RRF_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("RRF_USAGE_FILE", str(tmp_path / "usage.json"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-not-a-real-key")
    job = tmp_path / "jobs" / JOB
    for folder in jobs_module.MARK_FOLDERS:
        (job / folder).mkdir(parents=True)
    for entry in WRITTEN:
        (job / "Photos" / entry["file"]).write_bytes(jpg_bytes())
    (job / "Photos" / "photo-manifest.json").write_text(json.dumps(
        {"job": JOB, "context": "2840 Brady Street, Davenport",
         "report_year": 2026, "caption_style": "view",
         "photos": [dict(e) for e in WRITTEN]}, indent=2))
    return tmp_path / "jobs"


@pytest.fixture
def client(home):
    return TestClient(create_app(), raise_server_exceptions=False)


def on_disk(job: Path) -> dict:
    return json.loads((job / "Photos" / "photo-manifest.json").read_text())


def by_file(manifest: dict) -> dict:
    return {e["file"]: e for e in manifest["photos"]}


def stand_in(monkeypatch, words="View of a newly written thing"):
    """A model that writes captions and never touches the network.

    The seam is `captions.draft_captions`, which is the one place in this app
    where money is spent, so standing in here is standing in for every paid
    path at once.
    """
    calls = {"n": 0, "paths": []}

    def fake(context, paths, style=None):
        calls["n"] += 1
        calls["paths"].append([p.name for p in paths])
        return ({p.name: words for p in paths}, dict(USED))

    monkeypatch.setattr(captions, "draft_captions", fake)
    return calls


# ------------------------------------------------- the clear keeps a copy ---
def test_the_clear_keeps_the_words_it_takes_off(client, home):
    job = home / JOB
    assert client.post("/api/jobs/%s/captions/clear" % JOB).status_code == 200

    kept = by_file(on_disk(job))
    assert kept["a.jpg"]["caption"] == ""
    assert kept["a.jpg"][photos_routes.CLEARED] == "View east from Brady Street"
    assert kept["b.jpg"][photos_routes.CLEARED] == "Rear loading area"


def test_a_photograph_that_had_no_caption_gains_no_copy(client, home):
    """A blank caption has nothing to keep, so nothing is written for it. The
    control on that tile therefore stays grey, which is the truth."""
    client.post("/api/jobs/%s/captions/clear" % JOB)
    assert photos_routes.CLEARED not in by_file(on_disk(home / JOB))["c.jpg"]


def test_the_clear_takes_the_tick_off_with_the_words(client, home):
    """A tick says he has read the caption on this photograph, and there is no
    caption on it any more. It survived the clear until 2026-09-17, which left
    a filled green tick under an empty caption box and a photograph counted as
    reviewed that nobody could have reviewed. Found on screen, not by a test.
    """
    job = home / JOB
    assert by_file(on_disk(job))["a.jpg"]["reviewed"] is True
    client.post("/api/jobs/%s/captions/clear" % JOB)
    assert not by_file(on_disk(job))["a.jpg"].get("reviewed")


def test_the_copy_is_kept_in_the_app_s_own_note_and_nowhere_else(client, home):
    """Nothing new appears on disk. The manifest is the app's own note for the
    job and it already holds every caption, so the spare sits in the entry
    beside the live one."""
    job = home / JOB
    before = sorted(p.name for p in (job / "Photos").iterdir())
    client.post("/api/jobs/%s/captions/clear" % JOB)
    assert sorted(p.name for p in (job / "Photos").iterdir()) == before


# --------------------------------------------- back, on one photograph -----
def test_back_on_one_photograph_puts_that_one_back(client, home):
    job = home / JOB
    client.post("/api/jobs/%s/captions/clear" % JOB)

    r = client.post("/api/jobs/%s/photos/a.jpg/caption/back" % JOB)
    assert r.status_code == 200

    kept = by_file(on_disk(job))
    assert kept["a.jpg"]["caption"] == "View east from Brady Street"
    assert kept["b.jpg"]["caption"] == ""          # only the one asked for


def test_back_does_not_bring_the_tick_with_it(client, home):
    """A caption put back is read again, every time. a.jpg was ticked before
    the clear and comes back unticked."""
    job = home / JOB
    assert by_file(on_disk(job))["a.jpg"]["reviewed"] is True

    client.post("/api/jobs/%s/captions/clear" % JOB)
    client.post("/api/jobs/%s/photos/a.jpg/caption/back" % JOB)

    back = by_file(on_disk(job))["a.jpg"]
    assert back["caption"] == "View east from Brady Street"
    assert not back.get("reviewed")


def test_back_works_without_the_job_wide_one_ever_being_pressed(client, home):
    """It stands on its own. Spenser, 2026-09-17."""
    job = home / JOB
    client.post("/api/jobs/%s/captions/clear" % JOB)
    client.post("/api/jobs/%s/photos/b.jpg/caption/back" % JOB)
    assert by_file(on_disk(job))["b.jpg"]["caption"] == "Rear loading area"


def test_back_is_refused_when_nothing_was_cleared_for_it(client, home):
    r = client.post("/api/jobs/%s/photos/a.jpg/caption/back" % JOB)
    assert r.status_code == 400


def test_back_is_refused_for_a_photograph_this_job_does_not_have(client, home):
    r = client.post("/api/jobs/%s/photos/nope.jpg/caption/back" % JOB)
    assert r.status_code == 404


def test_the_copy_survives_being_put_back(client, home):
    """Back stays available. He can put it back, type over it, and put it back
    again, which is what a control that works on its own has to allow."""
    job = home / JOB
    client.post("/api/jobs/%s/captions/clear" % JOB)
    client.post("/api/jobs/%s/photos/a.jpg/caption/back" % JOB)
    assert by_file(on_disk(job))["a.jpg"][photos_routes.CLEARED] \
        == "View east from Brady Street"


# ------------------------------------- the job-wide back, and its sparing ---
def test_the_job_wide_back_puts_the_still_empty_ones_back(client, home):
    job = home / JOB
    client.post("/api/jobs/%s/captions/clear" % JOB)

    r = client.post("/api/jobs/%s/captions/back" % JOB)
    assert r.status_code == 200 and r.json()["back"] == 2

    kept = by_file(on_disk(job))
    assert kept["a.jpg"]["caption"] == "View east from Brady Street"
    assert kept["b.jpg"]["caption"] == "Rear loading area"


def test_the_job_wide_back_spares_what_he_typed_after_the_clear(client, home):
    """The decision that makes this safe. He clears, types a new caption on
    one photograph, then presses the job-wide back: the others come back and
    his own words are left exactly as he typed them."""
    job = home / JOB
    client.post("/api/jobs/%s/captions/clear" % JOB)

    manifest = client.get("/api/jobs/%s/manifest" % JOB).json()
    for entry in manifest["photos"]:
        if entry["file"] == "b.jpg":
            entry["caption"] = "Something he typed himself"
    assert client.put("/api/jobs/%s/manifest" % JOB, json=manifest).status_code == 200

    assert client.post("/api/jobs/%s/captions/back" % JOB).json()["back"] == 1

    kept = by_file(on_disk(job))
    assert kept["a.jpg"]["caption"] == "View east from Brady Street"
    assert kept["b.jpg"]["caption"] == "Something he typed himself"


def test_the_job_wide_back_spares_what_was_refreshed_after_the_clear(
        client, home, monkeypatch):
    stand_in(monkeypatch, words="A caption written again")
    job = home / JOB
    client.post("/api/jobs/%s/captions/clear" % JOB)
    assert client.post("/api/jobs/%s/photos/b.jpg/caption" % JOB).status_code == 200

    assert client.post("/api/jobs/%s/captions/back" % JOB).json()["back"] == 1
    assert by_file(on_disk(job))["b.jpg"]["caption"] == "A caption written again"


def test_pressing_the_job_wide_back_twice_changes_nothing(client, home):
    """Safe to press twice. The second press finds nothing still empty and
    says so rather than acting."""
    job = home / JOB
    client.post("/api/jobs/%s/captions/clear" % JOB)
    client.post("/api/jobs/%s/captions/back" % JOB)
    after_one = on_disk(job)

    second = client.post("/api/jobs/%s/captions/back" % JOB)
    assert second.status_code == 400
    assert on_disk(job) == after_one


def test_the_job_wide_back_takes_no_tick_back_with_it(client, home):
    job = home / JOB
    client.post("/api/jobs/%s/captions/clear" % JOB)
    client.post("/api/jobs/%s/captions/back" % JOB)
    assert not by_file(on_disk(job))["a.jpg"].get("reviewed")


def test_the_job_wide_back_is_refused_before_any_clear(client, home):
    assert client.post("/api/jobs/%s/captions/back" % JOB).status_code == 400


def test_it_reaches_every_photograph_the_clear_reached(client, home):
    """The clear blanks every caption in the file, including a photograph the
    screen is not currently drawing because the report comes from a different
    folder. The back has to reach the same ones, or the two are not each
    other's opposite and a caption is quietly left empty where nobody looks.
    """
    job = home / JOB
    path = job / "Photos" / "photo-manifest.json"
    manifest = json.loads(path.read_text())
    # A photograph with no file on disk, so the reconciled view drops it. It
    # is exactly the case where going through the view would lose the words.
    manifest["photos"].append({"file": "somewhere-else.jpg",
                               "caption": "A caption in another folder"})
    path.write_text(json.dumps(manifest, indent=2))

    client.post("/api/jobs/%s/captions/clear" % JOB)
    assert by_file(on_disk(job))["somewhere-else.jpg"]["caption"] == ""

    client.post("/api/jobs/%s/captions/back" % JOB)
    assert by_file(on_disk(job))["somewhere-else.jpg"]["caption"] \
        == "A caption in another folder"


def test_a_second_clear_does_not_empty_the_spares(client, home):
    """He clears, puts one back, deletes it by hand, then clears again. The
    photograph he emptied himself keeps the words it still had waiting."""
    job = home / JOB
    client.post("/api/jobs/%s/captions/clear" % JOB)
    client.post("/api/jobs/%s/photos/a.jpg/caption/back" % JOB)

    manifest = client.get("/api/jobs/%s/manifest" % JOB).json()
    for entry in manifest["photos"]:
        if entry["file"] == "a.jpg":
            entry["caption"] = ""
    client.put("/api/jobs/%s/manifest" % JOB, json=manifest)

    # There is one caption left in the job to clear, so the clear is allowed.
    manifest = client.get("/api/jobs/%s/manifest" % JOB).json()
    for entry in manifest["photos"]:
        if entry["file"] == "c.jpg":
            entry["caption"] = "A caption on the third one"
    client.put("/api/jobs/%s/manifest" % JOB, json=manifest)
    client.post("/api/jobs/%s/captions/clear" % JOB)

    assert by_file(on_disk(job))["a.jpg"][photos_routes.CLEARED] \
        == "View east from Brady Street"


# ------------------------------------- refresh, one photograph, one call ----
def test_refresh_writes_one_caption_with_one_model_call(client, home, monkeypatch):
    calls = stand_in(monkeypatch, words="View of the north elevation")
    job = home / JOB

    r = client.post("/api/jobs/%s/photos/a.jpg/caption" % JOB)
    assert r.status_code == 200 and r.json()["written"] is True

    assert calls["n"] == 1
    assert calls["paths"] == [["a.jpg"]]
    assert by_file(on_disk(job))["a.jpg"]["caption"] == "View of the north elevation"


def test_refresh_writes_over_a_caption_that_is_already_there(client, home, monkeypatch):
    """That is what it is for: the caption he does not like."""
    stand_in(monkeypatch, words="Different words entirely")
    job = home / JOB
    client.post("/api/jobs/%s/photos/b.jpg/caption" % JOB)
    assert by_file(on_disk(job))["b.jpg"]["caption"] == "Different words entirely"


def test_refresh_takes_the_tick_off(client, home, monkeypatch):
    """New words have not been read. a.jpg is ticked before this and is not
    ticked after it."""
    stand_in(monkeypatch)
    job = home / JOB
    assert by_file(on_disk(job))["a.jpg"]["reviewed"] is True
    client.post("/api/jobs/%s/photos/a.jpg/caption" % JOB)
    assert not by_file(on_disk(job))["a.jpg"].get("reviewed")


def test_refresh_touches_no_other_photograph(client, home, monkeypatch):
    stand_in(monkeypatch, words="Only this one changed")
    job = home / JOB
    client.post("/api/jobs/%s/photos/a.jpg/caption" % JOB)
    kept = by_file(on_disk(job))
    assert kept["b.jpg"]["caption"] == "Rear loading area"
    assert kept["c.jpg"]["caption"] == ""


def test_refresh_leaves_a_waiting_copy_alone(client, home, monkeypatch):
    """A refreshed photograph still has somewhere to go back to."""
    stand_in(monkeypatch, words="Newly written")
    job = home / JOB
    client.post("/api/jobs/%s/captions/clear" % JOB)
    client.post("/api/jobs/%s/photos/a.jpg/caption" % JOB)
    assert by_file(on_disk(job))["a.jpg"][photos_routes.CLEARED] \
        == "View east from Brady Street"


def test_refresh_is_refused_for_a_photograph_this_job_does_not_have(
        client, home, monkeypatch):
    calls = stand_in(monkeypatch)
    assert client.post("/api/jobs/%s/photos/nope.jpg/caption" % JOB).status_code == 404
    assert calls["n"] == 0                       # refused before anything was sent


def test_refresh_costs_nothing_when_there_is_no_key(client, home, monkeypatch):
    """The refusal is reached before a client can exist, the same order the
    whole-job run uses and for the same reason."""
    def explode(*a, **k):
        raise AssertionError("a model call was made after the key check")

    monkeypatch.setattr(captions, "draft_captions", explode)
    monkeypatch.setattr(captions, "ai_available", lambda: False)
    assert client.post("/api/jobs/%s/photos/a.jpg/caption" % JOB).status_code == 409


def test_refresh_records_what_it_spent(client, home, monkeypatch, tmp_path):
    """Money spent belongs in the history he can read, and the learned rate
    has to hear about a single photograph exactly as it hears about sixty."""
    stand_in(monkeypatch)
    client.post("/api/jobs/%s/photos/a.jpg/caption" % JOB)

    import usage as usage_store
    runs = usage_store.runs()
    assert runs, "a paid call was not recorded"
    assert runs[-1]["photos_requested"] == 1
    assert runs[-1]["photos_captioned"] == 1
    assert runs[-1]["api_requests"] == 1


# ----------------------------------------------- what one photograph costs --
def test_the_price_of_one_photograph_rides_on_the_estimate(client, home):
    """One question for sixty tiles. It is not a route of its own, because a
    figure printed on every tile must never become a question per tile: this
    app already shipped a fault where the price was asked for on every
    keystroke."""
    quote = client.get("/api/jobs/%s/caption-estimate" % JOB).json()
    assert quote["one_photo"]["photos"] == 1
    assert quote["one_photo"]["total"] > 0


def test_the_price_is_read_through_the_pricing_code(client, home):
    """Read, never copied. Another builder is changing the rounding right now,
    and this has to be correct either way, so it is compared against the
    pricing code rather than against a number written down here."""
    import cost
    quote = client.get("/api/jobs/%s/caption-estimate" % JOB).json()
    assert quote["one_photo"]["total"] == cost.estimate(1)["total"]


# ------------------------------------------- the shape of the row he asked --
# These read the stylesheet. They do not measure pixels: the two row widths are
# measured in a browser and written into the rule's own comment, and how it
# looks is checked by eye on the real app. What these guard is that each rule
# exists at all, because each was a thing Spenser asked for in words on
# 2026-09-17 and each could be undone without anything else noticing.
CSS = Path(__file__).resolve().parents[1] / "web" / "src" / "brand.css"


def rules(selector: str) -> list:
    """Every rule in the stylesheet with exactly this selector.

    Every one, not the first and not the last. `.review-line` is written three
    times: where it was born, where it is fitted inside the photograph, and
    inside a media query. A test that reads one of the three at random is a
    test that passes for the wrong reason.

    Comments come out first. These rules explain themselves at length and name
    the very declarations they no longer have, so a test looking for a
    declaration would find it in the sentence saying it was taken away.
    """
    css = re.sub(r"/\*.*?\*/", "", CSS.read_text(), flags=re.S)
    found, at = [], 0
    while True:
        try:
            at = css.index(selector + " {", at)
        except ValueError:
            return found
        shut = css.index("}", at)
        found.append(css[at:shut])
        at = shut


def test_the_row_is_evenly_spaced_edge_to_edge():
    """Spenser: *"Can we space those all out so they're evenly spaced? The
    check, the A, B, and the C refresh are all evenly spaced."*
    `space-between` is what does it: every gap gets the same share of the
    spare width, so no single gap can swallow it."""
    written = rules(".review-line")
    assert written, "the row has no rule of its own"
    assert any("space-between" in one for one in written), \
        "nothing spreads the row across the photograph"


def test_nothing_on_the_row_pushes_itself_to_one_end():
    """An automatic margin on this row is the fault he saw: it takes all the
    spare width into one gap and leaves the other four at the floor. It is
    the whole reason the row looked unevenly spaced."""
    for selector in (".review-line", ".dot", ".back-dot", ".refresh-dot",
                     ".tick-dot", ".band-dot"):
        for one in rules(selector):
            assert "margin-left: auto" not in one, \
                "%s pushes itself to one end again" % selector


def test_the_refresh_mark_is_bigger_than_the_price_beside_it():
    """He asked for the mark bigger and the number smaller in one sentence, so
    they are read as the pair he said."""
    mark = int(re.search(r"height:\s*(\d+)px", rules(".refresh-dot svg")[0]).group(1))
    price = float(re.search(r"font-size:\s*([\d.]+)px",
                            rules(".refresh-dot .price")[0]).group(1))
    assert mark >= 16, "the refresh mark is the smallest thing on the row again"
    assert price <= 11, "the price is not smaller than it was"
    assert mark > price


def test_every_control_on_the_row_is_the_same_height():
    """The circles are 26 by 26 and the refresh pill is 26 tall because it is
    a `.dot` too. Nothing on this row may set a height of its own, which is
    the only way one of them could stop being level with the rest."""
    circle = rules(".dot")[0]
    assert "height: 26px" in circle and "width: 26px" in circle
    for selector in (".back-dot", ".refresh-dot"):
        for one in rules(selector):
            assert "height:" not in one, \
                "%s sets a height, so it can stop matching the circles" % selector

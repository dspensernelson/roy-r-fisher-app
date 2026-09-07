"""Bands: the letters a job's photo sections are known by.

Slice 1 of docs/plans/2026-09-07-photo-bands.md. Nothing on screen reads any
of this yet. What is proved here is the shape on disk and the one rule that
cannot be got wrong later: a band's letter is assigned once and never moves.

The rule matters because the letter is what every photograph carries. Relabel
a band and every photograph pointing at it is suddenly pointing somewhere
else, silently, in a file nobody looks at.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

from docx import Document  # noqa: E402
from PIL import Image  # noqa: E402

import photos as photos_routes  # noqa: E402
from main import create_app  # noqa: E402
from photo_pages import build_photo_docx  # noqa: E402

from conftest import TEMPLATE_DOCX, has_template  # noqa: E402


@pytest.fixture
def job(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path / "jobs"))
    here = tmp_path / "jobs" / "A job"
    (here / "Photos").mkdir(parents=True)
    (here / "Photos" / "a.jpg").write_bytes(b"pretend jpeg")
    return here


# The manifest of a job that has never seen a band. Every job on Mark's
# machine looks like this today.
BEFORE_BANDS = {
    "job": "A job",
    "caption_style": "view",
    "photos": [{"file": "a.jpg", "caption": "View east"}],
}


def test_a_job_written_before_bands_reads_as_bands_off():
    """Absent means off, the same answer `is_cut` and `is_reviewed` give.

    This is the whole migration story: there is nothing to convert on disk and
    nothing to guess at.
    """
    assert photos_routes.bands_on(BEFORE_BANDS) is False
    assert photos_routes.band_list(BEFORE_BANDS) == []
    assert photos_routes.band_of(BEFORE_BANDS["photos"][0]) is None


def test_the_letter_is_the_first_letter_of_the_name():
    assert photos_routes.letter_for("Warehouse", []) == "W"
    assert photos_routes.letter_for("warehouse", []) == "W"


def test_the_band_that_was_there_first_keeps_its_letter():
    """F6's own example. Warehouse keeps W when Workshop arrives and takes Wo.

    This is the test the frozen-letter rule exists for: the new band bends
    around the old one, never the other way round.
    """
    assert photos_routes.letter_for("Workshop", ["W"]) == "Wo"


def test_a_third_collision_takes_a_third_letter():
    assert photos_routes.letter_for("Workroom", ["W", "Wo"]) == "Wor"


def test_a_typed_band_never_takes_a_locked_letter():
    """A, B and C are spoken for before Mark types anything."""
    assert photos_routes.letter_for("Attic", ["A", "B", "C"]) == "At"


def test_a_name_with_no_letters_left_to_give_takes_a_number():
    """Two bands named the same, or a one-letter name that collides. The
    letter still has to come out unique, because it is what the photographs
    point at."""
    assert photos_routes.letter_for("W", ["W"]) == "W2"
    assert photos_routes.letter_for("W", ["W", "W2"]) == "W3"


def test_a_band_a_photograph_points_at_must_exist(job):
    """An unknown letter is an error, not a silent drop.

    Quietly unassigning the photograph would hide the fault that wrote it,
    which is the same reason this refuses a file that resolves outside Photos
    rather than dropping it.
    """
    bad = {
        "photos": [{"file": "a.jpg", "caption": "", "band": "Z"}],
        "bands_on": True,
        "bands": [{"letter": "A", "name": "First", "locked": True}],
    }
    error = photos_routes._validate_manifest_shape(job, bad)
    assert error and "Z" in error


def test_a_photograph_in_a_band_that_exists_is_fine(job):
    good = {
        "photos": [{"file": "a.jpg", "caption": "", "band": "A"}],
        "bands_on": True,
        "bands": [{"letter": "A", "name": "First", "locked": True}],
    }
    assert photos_routes._validate_manifest_shape(job, good) is None


def test_the_toggle_is_true_or_false(job):
    error = photos_routes._validate_manifest_shape(
        job, {"photos": [{"file": "a.jpg", "caption": ""}], "bands_on": "yes"})
    assert error and "true or false" in error


def test_a_band_needs_a_letter_and_a_name(job):
    for band in ({"name": "First"}, {"letter": "A"}, {"letter": "", "name": "First"}):
        error = photos_routes._validate_manifest_shape(
            job, {"photos": [{"file": "a.jpg", "caption": ""}],
                  "bands_on": True, "bands": [band]})
        assert error, band


def test_a_job_with_no_bands_still_validates(job):
    """Nothing added here may make an existing manifest illegal."""
    assert photos_routes._validate_manifest_shape(job, BEFORE_BANDS) is None


# ---------------------------------------------------------------------------
# Slice 2: a band click resorts the list itself.
#
# The array is the one ordering fact in the app. `included()` reads it for
# captions, the preview and the build, so a sort applied at read time would
# leave the order on disk and the order in the report saying different things.
# Constraint 2 of F6 exists to stop that, and these are its tests.
# ---------------------------------------------------------------------------

TWO_BANDS = [{"letter": "A", "name": "First", "locked": True},
             {"letter": "C", "name": "Last", "locked": True}]


def with_bands(photos, on=True):
    return {"job": "A job", "bands_on": on,
            "bands": [dict(b) for b in TWO_BANDS], "photos": photos}


def order(manifest):
    return [e["file"] for e in manifest["photos"]]


def test_a_band_click_moves_the_photograph_in_the_list():
    m = with_bands([{"file": "a.jpg", "band": "C"},
                    {"file": "b.jpg", "band": "A"}])
    photos_routes.sort_by_band(m)
    assert order(m) == ["b.jpg", "a.jpg"]


def test_where_a_photograph_sits_inside_its_band_is_left_alone():
    """Band order, then the order it already had. Clicking a band answers one
    question and must not silently answer the other."""
    m = with_bands([{"file": "a.jpg", "band": "A"},
                    {"file": "b.jpg", "band": "C"},
                    {"file": "c.jpg", "band": "A"}])
    photos_routes.sort_by_band(m)
    assert order(m) == ["a.jpg", "c.jpg", "b.jpg"]


def test_a_photograph_with_no_band_waits_after_every_band():
    m = with_bands([{"file": "a.jpg"}, {"file": "b.jpg", "band": "C"}])
    photos_routes.sort_by_band(m)
    assert order(m) == ["b.jpg", "a.jpg"]


def test_with_bands_off_nothing_moves():
    """Constraint 1. Turning bands off reorders nothing, so a job can leave
    them behind as easily as it took them up."""
    m = with_bands([{"file": "a.jpg", "band": "C"},
                    {"file": "b.jpg", "band": "A"}], on=False)
    photos_routes.sort_by_band(m)
    assert order(m) == ["a.jpg", "b.jpg"]


def test_a_cut_photograph_keeps_its_band_and_sorts_with_it():
    """F6's edge, decided 2026-09-02: uncutting puts it back where it belongs
    rather than wherever the list happened to have room."""
    m = with_bands([{"file": "a.jpg", "band": "C"},
                    {"file": "b.jpg", "band": "A", "cut": True},
                    {"file": "c.jpg", "band": "A"}])
    photos_routes.sort_by_band(m)
    assert order(m) == ["b.jpg", "c.jpg", "a.jpg"]
    assert [e["file"] for e in photos_routes.included(m)] == ["c.jpg", "a.jpg"]


def test_included_still_answers_exactly_what_it_answered_before():
    """The list a job has today, run through the new sort, comes back
    untouched. Nothing added in this slice may change a job that has no
    bands."""
    before = [dict(e) for e in BEFORE_BANDS["photos"]]
    m = dict(BEFORE_BANDS, photos=[dict(e) for e in BEFORE_BANDS["photos"]])
    photos_routes.sort_by_band(m)
    assert m["photos"] == before
    assert photos_routes.included(m) == before


# ---------------------------------------------------------------------------
# The click itself, through the API Mark's screen will use.
# ---------------------------------------------------------------------------

BANDED = {
    "job": "A job",
    "caption_style": "view",
    "bands_on": True,
    "bands": [{"letter": "A", "name": "First", "locked": True},
              {"letter": "C", "name": "Last", "locked": True}],
    "photos": [{"file": "a.jpg", "caption": "one"},
               {"file": "b.jpg", "caption": "two"},
               {"file": "c.jpg", "caption": "three"}],
}


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path / "jobs"))
    where = tmp_path / "jobs" / "A job" / "Photos"
    where.mkdir(parents=True)
    for entry in BANDED["photos"]:
        (where / entry["file"]).write_bytes(b"pretend jpeg " + entry["file"].encode())
    (where / "photo-manifest.json").write_text(json.dumps(BANDED, indent=2))
    return tmp_path / "jobs"


@pytest.fixture
def client(home):
    return TestClient(create_app())


def on_disk(home) -> dict:
    return json.loads((home / "A job" / "Photos" / "photo-manifest.json").read_text())


def test_one_click_puts_a_photograph_in_a_band_and_moves_it(client, home):
    r = client.post("/api/jobs/A job/photos/c.jpg/band", json={"band": "A"})
    assert r.status_code == 200
    assert [e["file"] for e in on_disk(home)["photos"]] == ["c.jpg", "a.jpg", "b.jpg"]


def test_the_order_on_disk_is_the_order_the_report_will_use(client, home):
    client.post("/api/jobs/A job/photos/c.jpg/band", json={"band": "A"})
    client.post("/api/jobs/A job/photos/b.jpg/band", json={"band": "C"})
    assert [e["file"] for e in on_disk(home)["photos"]] == ["c.jpg", "b.jpg", "a.jpg"]


def test_a_click_touches_the_band_and_nothing_else(client, home):
    assert client.post("/api/jobs/A job/photos/c.jpg/band",
                       json={"band": "A"}).status_code == 200
    after = on_disk(home)["photos"]
    assert {e["file"]: e["caption"] for e in after} == {
        "a.jpg": "one", "b.jpg": "two", "c.jpg": "three"}
    assert [e.get("band") for e in after] == ["A", None, None]


def test_a_photograph_can_be_put_back_in_the_unassigned_strip(client, home):
    assert client.post("/api/jobs/A job/photos/a.jpg/band",
                       json={"band": "A"}).status_code == 200
    assert [e for e in on_disk(home)["photos"] if e["file"] == "a.jpg"][0]["band"] == "A"
    assert client.post("/api/jobs/A job/photos/a.jpg/band",
                       json={"band": None}).status_code == 200
    entry = [e for e in on_disk(home)["photos"] if e["file"] == "a.jpg"][0]
    assert "band" not in entry, "unassigning removes the key rather than writing an empty one"


def test_a_band_this_job_does_not_have_is_refused(client, home):
    r = client.post("/api/jobs/A job/photos/a.jpg/band", json={"band": "Z"})
    assert r.status_code == 400
    assert "Z" in r.json()["detail"]


def test_a_photograph_this_job_does_not_have_is_refused(client):
    r = client.post("/api/jobs/A job/photos/nope.jpg/band", json={"band": "A"})
    assert r.status_code == 404
    # The same sentence the reviewed and cut routes give, rather than the
    # bare 404 a missing route would answer with.
    assert r.json()["detail"] == "That photo is not in this job."


# ---------------------------------------------------------------------------
# The proof that bands are not a second ordering system.
# ---------------------------------------------------------------------------

def _job_with_photos(where: Path, names) -> Path:
    where.mkdir(parents=True)
    for i, n in enumerate(names):
        Image.new("RGB", (400, 300), (i * 40 % 255, 90, 120)).save(where / n)
    return where


def _build(where: Path, photos) -> list:
    """Build the photo pages and read the captions back in page order."""
    manifest = where / "photo-manifest.json"
    manifest.write_text(json.dumps({
        "job": "TESTJOB", "context": "123 Test St, Davenport, Iowa",
        "report_year": 2026, "photos": photos,
    }))
    out = build_photo_docx(manifest, TEMPLATE_DOCX)
    doc = Document(str(out))
    return [r.cells[1].text.strip() for t in doc.tables for r in t.rows]


@has_template
def test_clicking_bands_builds_the_same_document_as_dragging(tmp_path):
    """The whole point of constraint 2, proved on a real document.

    Two routes to one order: dragging the photographs into place, and leaving
    them in capture order while clicking a band under each. The pages that
    come out have to be the same, because the build knows nothing about bands
    and never should.
    """
    names = ["a.jpg", "b.jpg", "c.jpg", "d.jpg"]
    caption = {n: "View of subject %s" % n[0] for n in names}

    dragged = _job_with_photos(tmp_path / "dragged", names)
    by_hand = [{"file": n, "caption": caption[n]} for n in ["c.jpg", "d.jpg", "a.jpg", "b.jpg"]]

    clicked = _job_with_photos(tmp_path / "clicked", names)
    banded = {
        "bands_on": True,
        "bands": [{"letter": "A", "name": "First", "locked": True},
                  {"letter": "C", "name": "Last", "locked": True}],
        # Capture order, untouched. Only the band under each has been clicked.
        "photos": [{"file": "a.jpg", "caption": caption["a.jpg"], "band": "C"},
                   {"file": "b.jpg", "caption": caption["b.jpg"], "band": "C"},
                   {"file": "c.jpg", "caption": caption["c.jpg"], "band": "A"},
                   {"file": "d.jpg", "caption": caption["d.jpg"], "band": "A"}],
    }
    photos_routes.sort_by_band(banded)

    assert _build(dragged, by_hand) == _build(clicked, banded["photos"])


# ---------------------------------------------------------------------------
# Slice 3: the switch, and the list of bands behind it.
#
# A job has no bands until Mark turns the switch on. One switch, and A, B and
# C arrive together. Spenser, 2026-09-07: they are not always there.
# ---------------------------------------------------------------------------

PLAIN = {
    "job": "A job",
    "caption_style": "view",
    "photos": [{"file": "a.jpg", "caption": "one"},
               {"file": "b.jpg", "caption": "two"},
               {"file": "c.jpg", "caption": "three"}],
}


@pytest.fixture
def plain_home(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path / "jobs"))
    where = tmp_path / "jobs" / "A job" / "Photos"
    where.mkdir(parents=True)
    for entry in PLAIN["photos"]:
        (where / entry["file"]).write_bytes(b"pretend jpeg " + entry["file"].encode())
    (where / "photo-manifest.json").write_text(json.dumps(PLAIN, indent=2))
    return tmp_path / "jobs"


@pytest.fixture
def plain(plain_home):
    return TestClient(create_app())


def letters(manifest) -> list:
    return [b["letter"] for b in manifest.get("bands", [])]


def test_a_job_has_no_bands_until_the_switch_goes_on(plain, plain_home):
    assert on_disk(plain_home).get("bands_on") in (None, False)
    assert on_disk(plain_home).get("bands") in (None, [])


def test_the_switch_brings_A_B_and_C_together(plain, plain_home):
    r = plain.put("/api/jobs/A job/bands", json={"bands_on": True})
    assert r.status_code == 200
    assert letters(on_disk(plain_home)) == ["A", "B", "C"]


def test_the_switch_moves_no_photograph(plain, plain_home):
    """Constraint 1. Everything loaded stays where it is and waits to be
    clicked."""
    assert plain.put("/api/jobs/A job/bands",
                     json={"bands_on": True}).status_code == 200
    assert [e["file"] for e in on_disk(plain_home)["photos"]] == \
        ["a.jpg", "b.jpg", "c.jpg"]


def test_the_switch_off_keeps_what_he_already_clicked(plain, plain_home):
    """Turning it off is not throwing it away. He can put it back on and find
    his work."""
    plain.put("/api/jobs/A job/bands", json={"bands_on": True})
    plain.post("/api/jobs/A job/photos/c.jpg/band", json={"band": "A"})
    plain.put("/api/jobs/A job/bands", json={"bands_on": False})
    kept = {e["file"]: e.get("band") for e in on_disk(plain_home)["photos"]}
    assert kept["c.jpg"] == "A"


def test_a_band_he_types_takes_its_letter_from_its_name(plain, plain_home):
    plain.put("/api/jobs/A job/bands", json={"bands_on": True})
    plain.put("/api/jobs/A job/bands", json={"bands": [
        {"letter": "A", "name": "A"}, {"letter": "B", "name": "B"},
        {"name": "Warehouse"}, {"letter": "C", "name": "C"}]})
    assert letters(on_disk(plain_home)) == ["A", "B", "W", "C"]


def test_renaming_a_band_does_not_move_its_letter(plain, plain_home):
    """Constraint 3, seen from the screen. Every photograph in that band
    points at the letter."""
    plain.put("/api/jobs/A job/bands", json={"bands_on": True})
    plain.put("/api/jobs/A job/bands", json={"bands": [
        {"letter": "A", "name": "A"}, {"letter": "B", "name": "B"},
        {"name": "Warehouse"}, {"letter": "C", "name": "C"}]})
    plain.post("/api/jobs/A job/photos/a.jpg/band", json={"band": "W"})
    plain.put("/api/jobs/A job/bands", json={"bands": [
        {"letter": "A", "name": "A"}, {"letter": "B", "name": "B"},
        {"letter": "W", "name": "Storage"}, {"letter": "C", "name": "C"}]})
    after = on_disk(plain_home)
    assert letters(after) == ["A", "B", "W", "C"]
    assert [b["name"] for b in after["bands"]] == ["A", "B", "Storage", "C"]
    assert [e for e in after["photos"] if e["file"] == "a.jpg"][0]["band"] == "W"


def test_A_B_and_C_cannot_be_taken_away(plain, plain_home):
    plain.put("/api/jobs/A job/bands", json={"bands_on": True})
    r = plain.put("/api/jobs/A job/bands", json={"bands": [
        {"letter": "A", "name": "A"}, {"letter": "C", "name": "C"}]})
    assert r.status_code == 400
    assert "B" in r.json()["detail"]
    assert letters(on_disk(plain_home)) == ["A", "B", "C"]


def test_a_band_this_job_never_had_cannot_arrive_with_a_letter(plain, plain_home):
    """A letter is given out by the app, once, and never chosen by the
    screen. This is how a reletter is refused."""
    plain.put("/api/jobs/A job/bands", json={"bands_on": True})
    r = plain.put("/api/jobs/A job/bands", json={"bands": [
        {"letter": "A", "name": "A"}, {"letter": "B", "name": "B"},
        {"letter": "Z", "name": "Warehouse"}, {"letter": "C", "name": "C"}]})
    assert r.status_code == 400
    assert "Z" in r.json()["detail"]


def test_nothing_goes_before_A_or_after_C(plain, plain_home):
    plain.put("/api/jobs/A job/bands", json={"bands_on": True})
    first = plain.put("/api/jobs/A job/bands", json={"bands": [
        {"name": "Warehouse"}, {"letter": "A", "name": "A"},
        {"letter": "B", "name": "B"}, {"letter": "C", "name": "C"}]})
    assert first.status_code == 400
    last = plain.put("/api/jobs/A job/bands", json={"bands": [
        {"letter": "A", "name": "A"}, {"letter": "B", "name": "B"},
        {"letter": "C", "name": "C"}, {"name": "Warehouse"}]})
    assert last.status_code == 400


def test_a_typed_band_may_sit_before_or_after_B(plain, plain_home):
    plain.put("/api/jobs/A job/bands", json={"bands_on": True})
    r = plain.put("/api/jobs/A job/bands", json={"bands": [
        {"letter": "A", "name": "A"}, {"name": "Warehouse"},
        {"letter": "B", "name": "B"}, {"letter": "C", "name": "C"}]})
    assert r.status_code == 200
    assert letters(on_disk(plain_home)) == ["A", "W", "B", "C"]


def test_taking_a_band_away_sends_its_photographs_back_to_waiting(plain, plain_home):
    """And moves nothing else. F6, 2026-09-02."""
    plain.put("/api/jobs/A job/bands", json={"bands_on": True})
    plain.put("/api/jobs/A job/bands", json={"bands": [
        {"letter": "A", "name": "A"}, {"letter": "B", "name": "B"},
        {"name": "Warehouse"}, {"letter": "C", "name": "C"}]})
    plain.post("/api/jobs/A job/photos/a.jpg/band", json={"band": "W"})
    plain.post("/api/jobs/A job/photos/b.jpg/band", json={"band": "B"})
    plain.put("/api/jobs/A job/bands", json={"bands": [
        {"letter": "A", "name": "A"}, {"letter": "B", "name": "B"},
        {"letter": "C", "name": "C"}]})
    after = on_disk(plain_home)
    kept = {e["file"]: e.get("band") for e in after["photos"]}
    assert kept["a.jpg"] is None, "its band is gone, so it waits again"
    assert kept["b.jpg"] == "B", "nothing else moved"
    assert letters(after) == ["A", "B", "C"]

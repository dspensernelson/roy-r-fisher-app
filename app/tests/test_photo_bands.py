"""Bands: the letters a job's photo sections are known by.

Slice 1 of docs/plans/2026-09-07-photo-bands.md. Nothing on screen reads any
of this yet. What is proved here is the shape on disk and the one rule that
cannot be got wrong later: a band's letter is assigned once and never moves.

The rule matters because the letter is what every photograph carries. Relabel
a band and every photograph pointing at it is suddenly pointing somewhere
else, silently, in a file nobody looks at.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import photos as photos_routes  # noqa: E402


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

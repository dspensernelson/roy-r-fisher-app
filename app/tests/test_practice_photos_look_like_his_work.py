"""The practice job has to look like the reports it stands in for.

Spenser found portrait photographs in the shipped practice jobs. Twelve of the
seventy-three, across both jobs.

They should never have been there. Not one photograph in any photo document
Mark delivers is portrait: Mason City fifty, 217 East 37th Street twenty-four,
Burlington six, every one landscape. The demo generator filtered only on file
size, over the whole of `Report Examples`, so it swept up sketches, market
overview images and anything else that was a JPEG of about the right weight.

The cost was not cosmetic. The demo was read as evidence about his reports, and
a change to how photographs are sized was built on top of it and reported as
the fix for a blank page it had nothing to do with. A practice job that lies
about the work is worse than no practice job.
"""
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageOps

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import photo_source  # noqa: E402

needs_corpus = pytest.mark.skipif(
    not photo_source.SOURCE.is_dir(),
    reason="the delivered reports are private and not on this machine")


def shape(path: Path):
    with Image.open(path) as opened:
        return ImageOps.exif_transpose(opened).size


@needs_corpus
def test_the_pool_the_practice_jobs_are_built_from_is_all_landscape():
    pool = photo_source.photographs()
    assert pool, "no photographs found at all"
    portrait = [p for p in pool if shape(p)[1] > shape(p)[0]]
    assert portrait == [], "%d portrait photographs are still selectable" % len(portrait)


@needs_corpus
def test_orientation_is_read_the_way_it_displays(tmp_path):
    """A photograph taken sideways is stored landscape with a flag saying so."""
    upright = tmp_path / "wide.jpg"
    Image.new("RGB", (1000, 750), (10, 20, 30)).save(upright)
    assert photo_source._is_landscape(upright)

    tall = tmp_path / "tall.jpg"
    Image.new("RGB", (750, 1000), (10, 20, 30)).save(tall)
    assert not photo_source._is_landscape(tall)


def test_a_file_that_cannot_be_opened_is_not_offered(tmp_path):
    broken = tmp_path / "not-really.jpg"
    broken.write_bytes(b"this is not an image")
    assert not photo_source._is_landscape(broken)


@needs_corpus
def test_a_built_practice_job_contains_no_portrait_photograph(tmp_path):
    """The end of it: build the jobs and look at what came out."""
    sys.path.insert(0, str(REPO / "tools"))
    import demo_job

    # build() returns the ordinary job; the folder holding both is its parent.
    demo_job.build(tmp_path)
    home = tmp_path / demo_job.DEMO_PARENT
    jobs = sorted(p for p in home.iterdir() if p.is_dir())
    assert jobs, "no practice jobs were built"
    for job in jobs:
        photos = sorted((job / "Photos").glob("*.jpg"))
        assert photos, job.name
        for photo in photos:
            width, height = shape(photo)
            assert width > height, "%s/%s is portrait" % (job.name, photo.name)

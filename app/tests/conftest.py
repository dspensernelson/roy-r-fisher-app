from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Mark's delivered reports and his own folder template. Private material: it
# is not in this repository and never will be, so every test that needs a
# piece of it says which piece and skips when it is not there.
#
# It moved next door on 2026-08-21, when the application repository was split
# out of the evidence vault, and this path did not follow it. The corpus was
# still on the machine and fifteen tests had been quietly skipping ever since,
# including the one that compares a built document against a delivered report.
# Both places are checked so the same suite works either side of that split and
# on a clone that has neither.
def _find_corpus() -> Path:
    beside = REPO_ROOT.parent / "RRF" / "Report Examples"
    inside = REPO_ROOT / "Report Examples"
    return inside if inside.is_dir() else beside


CORPUS = _find_corpus()
TEMPLATE_DOCX = CORPUS / "Templates and Other" / "Mark Folder Template" / "Photos" / "Photo.docx"
GOLDEN_PHOTOS = (CORPUS / "MASON CITY_Walmart_4151 4th St SW" / "Photos"
                 / "Raw pics_Walmart Mason City 4151 4th St SW" / "All report photos used")
GOLDEN_DELIVERED = (CORPUS / "MASON CITY_Walmart_4151 4th St SW" / "Photos"
                    / "PHOTOS_Mason City_ 4151_4th_St_SW_(Walmart).docx")


def _golden_ready() -> bool:
    """The Mason City photos and the delivered document the golden test
    compares against. Checked properly, because the photos live inside a
    Photos folder and .gitignore excludes those by design."""
    if not GOLDEN_DELIVERED.is_file() or not GOLDEN_PHOTOS.is_dir():
        return False
    return len(list(GOLDEN_PHOTOS.glob("*.jpeg"))) >= 12


# Checking the corpus ROOT was not enough and quietly cost a test run. The
# root is tracked, so on a fresh clone it exists while everything inside a
# Photos folder does not, and the guard passed while the test failed. Each
# guard now checks the exact file the tests behind it open.
has_template = pytest.mark.skipif(
    not TEMPLATE_DOCX.is_file(),
    reason="Mark's folder template is private and not in this repository",
)

has_golden_corpus = pytest.mark.skipif(
    not (TEMPLATE_DOCX.is_file() and _golden_ready()),
    reason="the Mason City delivered report and its photos are private and not in this repository",
)


@pytest.fixture(autouse=True)
def never_touch_the_real_home(tmp_path_factory, monkeypatch):
    """No test may write into Spenser's own home folder.

    Found the hard way. A job the app creates is now marked active, which
    writes the settings file, and tests that only overrode RRF_JOBS_HOME
    wrote into his real ~/.rrf-app.json instead. Forty entries pointing at
    pytest temporary folders ended up in it. A test that reaches outside its
    own tmp_path is a bug in the test, so this closes the door for all of
    them at once rather than one file at a time.
    """
    box = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("RRF_SETTINGS_FILE", str(box / ".rrf-app.json"))
    monkeypatch.setenv("RRF_KEY_FILE", str(box / ".rrf-app.env"))
    # Every app-owned file, not only the two that already existed. The
    # classification store was missing from this list and only individual
    # tests overrode it, so any test that classified a file without setting
    # RRF_CLASSIFY_FILE itself wrote into his real home. Task 2 added three
    # more of these, and one forgotten line here would put every one of them
    # in the same position, so the list is kept complete rather than added to
    # a test at a time.
    monkeypatch.setenv("RRF_CLASSIFY_FILE", str(box / ".rrf-classifications.json"))
    monkeypatch.setenv("RRF_VERSION_FILE", str(box / ".rrf-app-version.json"))
    monkeypatch.setenv("RRF_USAGE_FILE", str(box / ".rrf-ai-usage.json"))
    monkeypatch.setenv("RRF_AI_POLICY_FILE", str(box / ".rrf-demo-ai-policy.json"))
    monkeypatch.setenv("RRF_JOBFACTS_FILE", str(box / ".rrf-job-facts.json"))
    # The thumbnail cache, added 2026-08-22 when thumbnails moved out of
    # Mark's Photos folder. Missing it did exactly what the comment above
    # predicts: every suite run left a fresh folder of thumbnails in the
    # real home directory, one per pytest tmp_path, accumulating for ever.
    monkeypatch.setenv("RRF_CACHE_DIR", str(box / ".rrf-app-cache"))


@pytest.fixture
def template_path() -> Path:
    return TEMPLATE_DOCX

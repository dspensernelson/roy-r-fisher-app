import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import jobs  # noqa: E402


def test_tax_appeal_matches_the_corpus_house_style():
    assert jobs.propose_folder_name("Mason City", "4151 4th St SW", "Tax appeal", 2026) == \
        "MASON CITY_4151 4th St SW - 2026 Tax"


def test_each_engagement_gets_its_measured_suffix():
    assert jobs.propose_folder_name("Davenport", "1757 W. 12th Street", "Rent study", 2026) == \
        "DAVENPORT_1757 W. 12th Street - Rent Study"
    assert jobs.propose_folder_name("Davenport", "4300 E 53rd Street", "Right of way", 2026) == \
        "DAVENPORT_4300 E 53rd Street ROW"
    assert jobs.propose_folder_name("Davenport", "5348 Elmore Circle", "Full appraisal", 2025) == \
        "DAVENPORT_5348 Elmore Circle - 2025"


def test_characters_windows_forbids_are_stripped():
    """Mark is on Windows. A name the app proposes has to be creatable there."""
    name = jobs.propose_folder_name("Davenport", 'A/B\\C:D*E?F"G<H>I|J', "Full appraisal", 2026)
    for bad in '<>:"/\\|?*':
        assert bad not in name
    assert jobs.SAFE_NAME.match(name)


def test_name_stays_within_the_safe_length_and_shape():
    name = jobs.propose_folder_name("Davenport", "X" * 300, "Full appraisal", 2026)
    assert len(name) <= 120
    assert jobs.SAFE_NAME.match(name)
    assert not name.endswith(".") and name == name.strip()


def test_a_blank_address_still_produces_something_usable():
    name = jobs.propose_folder_name("", "", "Tax appeal", 2026)
    assert name and jobs.SAFE_NAME.match(name)

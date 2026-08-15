import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import sections  # noqa: E402

MATRIX_PRESENT = pytest.mark.skipif(
    not sections.MATRIX.is_file(), reason="shop engagement matrix not present"
)


@MATRIX_PRESENT
def test_tax_appeal_proposes_the_measured_spine():
    result = sections.propose("Tax appeal")
    names = [s["name"] for s in result["sections"]]
    on = [s["name"] for s in result["sections"] if s["default"]]
    for expected in ["Title Page", "Letter of Transmittal", "Subject Photographs",
                     "Statement of Appraisal Problem", "Salient Facts Summary",
                     "Site Analysis", "Sales Comparison Approach", "Income Approach",
                     "Correlation", "Certification", "Limiting Conditions", "Addenda"]:
        assert expected in on, f"{expected} should be proposed for a tax appeal"
    assert "Assessment and Taxes" not in names        # folds into Salient Facts
    assert result["thin_evidence"] is False


@MATRIX_PRESENT
def test_row_drops_the_approaches_the_corpus_drops():
    on = [s["name"] for s in sections.propose("Right of way")["sections"] if s["default"]]
    assert "Income Approach" not in on
    assert "Sales Comparison Approach" in on
    assert sections.propose("Right of way")["thin_evidence"] is True


@MATRIX_PRESENT
def test_rent_study_is_thin_and_narrow():
    result = sections.propose("Rent study")
    on = [s["name"] for s in result["sections"] if s["default"]]
    assert result["thin_evidence"] is True
    assert "Income Approach" in on
    assert "Cost Approach" not in on
    assert "Neighborhood Description" not in on


@MATRIX_PRESENT
def test_qualified_rows_are_offered_but_not_checked():
    result = sections.propose("Tax appeal")
    regional = [s for s in result["sections"] if s["name"] == "Regional and City Data"]
    assert regional and regional[0]["default"] is False   # "out-of-metro only"


@MATRIX_PRESENT
def test_title_row_splits_into_two_real_sections():
    names = [s["name"] for s in sections.propose("Full appraisal")["sections"]]
    assert "Title Page" in names and "Letter of Transmittal" in names
    assert "Title + transmittal" not in names


def test_unknown_engagement_is_rejected():
    with pytest.raises(ValueError):
        sections.propose("Divorce appraisal")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import brief  # noqa: E402


def test_write_then_read_round_trip(tmp_path):
    job = tmp_path / "MASON CITY_4151 4th St SW"
    job.mkdir()
    brief.write_brief(
        job,
        {"Property address": "4151 4th St SW, Mason City, Iowa",
         "Property type": "retail",
         "Engagement type": "Tax appeal"},
        ["Title Page", "Subject Photographs", "Salient Facts Summary"],
    )
    got = brief.read_brief(job)
    assert got["fields"]["Property address"] == "4151 4th St SW, Mason City, Iowa"
    assert got["fields"]["Property type"] == "retail"
    assert got["sections"] == ["Title Page", "Subject Photographs", "Salient Facts Summary"]


def test_missing_brief_reads_as_empty(tmp_path):
    job = tmp_path / "NO BRIEF"
    job.mkdir()
    assert brief.read_brief(job) == {"fields": {}, "sections": []}


def test_write_keeps_earlier_fields_and_replaces_sections(tmp_path):
    job = tmp_path / "JOB"
    job.mkdir()
    brief.write_brief(job, {"Property address": "1 Main St", "Client (intended user)": "City"}, ["A", "B"])
    brief.write_brief(job, {"Report due date": "June 15, 2026"}, ["A"])
    got = brief.read_brief(job)
    assert got["fields"]["Property address"] == "1 Main St"      # earlier value survives
    assert got["fields"]["Client (intended user)"] == "City"
    assert got["fields"]["Report due date"] == "June 15, 2026"   # new value lands
    assert got["sections"] == ["A"]                              # sections replaced, not merged


def test_fee_is_pointer_only_and_never_takes_a_number(tmp_path):
    job = tmp_path / "JOB"
    job.mkdir()
    brief.write_brief(job, {"Property address": "1 Main St", "Fee": "$4,500"}, [])
    text = brief.brief_path(job).read_text()
    assert "$4,500" not in text
    assert "engagement letter" in text.lower()


def test_a_dollar_amount_cannot_ride_in_on_any_other_field(tmp_path):
    """The fee rule is about the brief, not about one row of it. A number
    typed into Client or Intended use is a drafting input just the same."""
    job = tmp_path / "JOB"
    job.mkdir()
    brief.write_brief(job, {
        "Property address": "1 Main St",
        "Client (intended user)": "City of Mason City, fee $4,500 per letter",
        "Intended use": "tax appeal, billed at $150/hr",
    }, [])
    got = brief.read_brief(job)["fields"]
    text = brief.brief_path(job).read_text()
    assert "$4,500" not in text and "$150" not in text
    # The rest of what he typed survives; only the amount is dropped.
    assert got["Client (intended user)"] == "City of Mason City, fee per letter"
    assert got["Intended use"] == "tax appeal, billed at /hr"


def test_reads_a_hand_written_brief_in_the_firms_format(tmp_path):
    job = tmp_path / "HAND MADE"
    job.mkdir()
    (job / "job-brief.md").write_text(
        "# Job Brief - HAND MADE\n\n## Assignment\n\n"
        "| Field | Value |\n|---|---|\n"
        "| Property address | 5515 Utica Ridge, Davenport, Iowa |\n"
        "| Engagement type | tax appeal |\n\n"
        "## Sections in this report\n\n"
        "| Section | Donor |\n|---|---|\n"
        "| Statement of the Appraisal Problem | Utica Ridge |\n"
        "| Site Analysis | Utica Ridge |\n"
    )
    got = brief.read_brief(job)
    assert got["fields"]["Engagement type"] == "tax appeal"
    assert got["sections"] == ["Statement of the Appraisal Problem", "Site Analysis"]

"""Finding the two sources, and refusing a value the sources do not carry.

The quote check is the one thing standing between a model's guess and a signed
appraisal, so it is tested on its own, with no model and no network.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conftest import CORPUS  # noqa: E402
from engine import improvements_read as read  # noqa: E402
from server import improvements as imp  # noqa: E402

BLAUL = CORPUS / "BURLINGTON_425 Valley St, (Blaul Lofts)"
needs_blaul = pytest.mark.skipif(
    not BLAUL.is_dir(),
    reason="Mark's Blaul Lofts job is private and not on this machine")


class Item:
    def __init__(self, quote, source):
        self.quote, self.source = quote, source


SOURCES = {
    "card": 'Ftg & Fdtn\n  Brick or Stone   20"\n  Windows  Wood Double Hung',
    "transcript": "the basement floor in a rock and rubble with some brick",
}


def test_a_value_whose_words_are_in_its_source_is_kept():
    kept, thrown = imp.verify([Item("Brick or Stone", "card")], SOURCES)
    assert [i.quote for i in kept] == ["Brick or Stone"]
    assert thrown == []


def test_a_value_whose_words_are_not_there_is_thrown_away():
    """Mark's own delivered Blaul report says granite. His transcript says hard
    surface, six times, and never granite. This is that mistake."""
    kept, thrown = imp.verify([Item("granite countertops", "transcript")], SOURCES)
    assert kept == []
    assert [i.quote for i in thrown] == ["granite countertops"]


def test_the_right_words_in_the_wrong_source_are_thrown_away():
    """Brick is in the card. Claiming the transcript said it is still a claim
    the app cannot point at."""
    kept, thrown = imp.verify([Item("Wood Double Hung", "transcript")], SOURCES)
    assert kept == [] and len(thrown) == 1


def test_spacing_and_case_and_punctuation_do_not_matter():
    """A PDF breaks words across columns and a transcript carries curly quotes.
    A check that respected either would reject values that really are there."""
    kept, _ = imp.verify([Item("brick   or\nstone,", "card")], SOURCES)
    assert len(kept) == 1


def test_an_empty_quote_proves_nothing():
    kept, thrown = imp.verify([Item("", "card"), Item("   ", "card")], SOURCES)
    assert kept == [] and len(thrown) == 2


@needs_blaul
def test_a_comparable_sale_card_is_never_offered_as_the_subject():
    """Measured 2026-08-28: this job holds four property record cards and three
    are comparable sales in other towns. Alphabetically a comp came first.
    Reading one would put another building's walls in Mark's report."""
    found = read.find_sources(BLAUL)
    names = [p.name for p in found["cards"]]
    assert names, "no assessor card found at all"
    assert not any("Moline" in n or "Des Moines_" in n for n in names), names
    assert "Blaul" in names[0], names


@needs_blaul
def test_the_transcript_for_this_section_is_offered_first():
    """The job carries a neighbourhood transcript too. It belongs to a
    different section and must not be the default here."""
    found = read.find_sources(BLAUL)
    first = found["transcripts"][0].name.lower()
    assert "improvement" in first, [p.name for p in found["transcripts"]]


@needs_blaul
def test_both_sources_read_into_text_the_check_can_search():
    found = read.find_sources(BLAUL)
    card = read.read_file(found["cards"][0])
    transcript = read.read_file(found["transcripts"][0])
    assert read.flatten(card).count("gba70607"), "the card lost its floor area"
    assert "sprinkler" in transcript.lower()
    kept, thrown = imp.verify(
        [Item("Solid Brick", "card"), Item("Sprinkler system has been installed", "transcript")],
        {"card": card, "transcript": transcript})
    assert len(kept) == 2 and thrown == []

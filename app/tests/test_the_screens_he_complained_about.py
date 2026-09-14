"""The three screen faults Mark named while testing 0.7.0 on Windows.

What this proves and what it does not. These read the stylesheet and the
screen's own source and assert the rules are there. They do not measure
pixels; how it looks is checked by eye on the real app. What they guard is
that the rule exists at all, because each of these three was a missing rule
rather than a wrong value.
"""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web" / "src"
CSS = WEB / "brand.css"
APP = WEB / "App.jsx"


def block(name: str) -> str:
    """One rule's declarations, by its selector."""
    css = CSS.read_text()
    start = css.index(name + " {")
    return css[start:css.index("}", start)]


# Settings drew five white cards with no space between them, so their borders
# touched and the screen read as one grey slab of text.

def test_a_settings_card_has_room_under_it():
    got = re.search(r"margin-bottom:\s*(\d+)px", block(".setting"))
    assert got, "the settings card needs a bottom margin or the cards touch"
    assert 12 <= int(got.group(1)) <= 24


def test_only_settings_uses_that_card():
    """So giving it a margin cannot open a gap on a screen nobody asked about."""
    users = [p for p in (WEB / "screens").glob("*.jsx")
             if "className=\"setting\"" in p.read_text() and ".test." not in p.name]
    assert [p.name for p in users] == ["Settings.jsx"]


# The dark bar carries the only way out of a job, and it scrolled away with
# the page. Thirty photographs is several screens tall.

def test_the_bar_stays_at_the_top_of_the_window():
    bar = block(".bar")
    assert "position: sticky" in bar
    assert re.search(r"top:\s*0", bar)
    assert re.search(r"z-index:\s*(\d+)", bar), "it has to sit over the page it covers"


def test_the_list_search_row_parks_under_the_bar_rather_than_behind_it():
    """The only other thing in the app that sticks to top: 0."""
    css = CSS.read_text()
    assert ":has(.bar) .picker-head" in css
    parked = block("body:has(.bar) .picker-head")
    assert "var(--bar-height)" in parked
    assert re.search(r"--bar-height:\s*\d+px", css), "one place for the bar's height"


# "we need to make it obvious these are not computer people." The job's own
# name was plain white text that only underlined on hover.

def test_both_ways_out_of_a_job_are_drawn_as_chips():
    chip = block(".bar-inner .crumb-chip")
    assert "border:" in chip
    assert "border-radius:" in chip
    app = APP.read_text()
    assert app.count('"crumb-chip"') == 2, "the way back to Jobs and to the job"
    assert "crumb-back" not in app and "crumb-back" not in CSS.read_text()

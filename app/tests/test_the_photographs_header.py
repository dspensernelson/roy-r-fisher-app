"""The photographs screen's header: the line under the title, and the row that
stays at the top while he scrolls.

Spenser's feedback from testing 0.7.6.3, 18 September 2026. Read from the
stylesheet, because these are layout rules and the Vitest screens do not lay
anything out. What they look like on screen was checked in a browser.
"""
import re
from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / "web" / "src" / "brand.css"


def rules(selector: str) -> list:
    """Every rule whose selector list names exactly this selector."""
    css = re.sub(r"/\*.*?\*/", "", CSS.read_text(), flags=re.S)
    out = []
    for sel, body in re.findall(r"([^{}]+)\{([^}]*)\}", css):
        names = [s.strip() for s in sel.split(",")]
        if selector in names:
            out.append(body)
    return out


def one(selector: str) -> str:
    got = rules(selector)
    assert got, "nothing styles %s" % selector
    return " ".join(got)


# --- 1. the progress bar under the title runs the width of its line ---------
def test_the_progress_bar_takes_the_room_its_line_has():
    """"Writing captions · 0 of 12 written" carried a 54px stub. It grows now,
    so it runs to the end of the line."""
    thread = one(".thread")
    assert re.search(r"flex:\s*1\b", thread), "the bar does not grow into its line"
    assert not re.search(r"(^|[;\s])width\s*:", thread), \
        "a fixed width would make it a stub again"


# --- 4. the title and widget row stays at the top while he scrolls ----------
HEAD = ".frame.is-photos .screen-head:not(.is-asking)"


def test_the_header_row_stays_at_the_top():
    head = one(HEAD)
    assert re.search(r"position:\s*sticky", head)
    # Under the dark bar, which is itself stuck to the top of the window.
    # `--bar-height` exists so the two agree on one number.
    assert re.search(r"top:\s*calc\(var\(--bar-height\)", head)


def test_photographs_do_not_show_through_it():
    head = one(HEAD)
    assert re.search(r"background:\s*var\(--ground\)", head)
    assert re.search(r"z-index:\s*\d", head)


def test_it_sits_below_the_dark_bar_and_never_over_it():
    bar = int(re.search(r"z-index:\s*(\d+)", one(".bar")).group(1))
    head = int(re.search(r"z-index:\s*(\d+)", one(HEAD)).group(1))
    assert head < bar


def test_a_plain_red_line_marks_where_it_ends():
    """In the app's red, the full width of the screen, and not a progress
    bar: nothing in it moves."""
    line = one(HEAD + "::after")
    assert "var(--brand)" in line
    assert "100vmax" in line, "the line stops at the frame instead of the screen"
    # 100vw counts the scrollbar on Windows and makes the page scroll sideways.
    assert "100vw" not in line
    assert "transition" not in line and "animation" not in line


def test_a_photograph_brought_into_view_lands_below_the_fixed_row():
    """Tabbing to a caption box, or anything that scrolls a photograph into
    view, stops it below the fixed row rather than under it."""
    page = one(":root:has(.frame.is-photos)")
    assert re.search(r"scroll-padding-top:\s*calc\(var\(--bar-height\)", page)

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

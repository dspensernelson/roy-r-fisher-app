"""AI or Typed sits in the upper left corner of the photograph.

Spenser, 2026-09-18, from 0.7.6.3: it moves off the caption line, where it
pushed everything down, and is laid quietly over the picture. It must not
cover the take-out button or anything he clicks.

Read from the stylesheet. Where it lands on screen was checked in a browser.
"""
import re
from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / "web" / "src" / "brand.css"


def rules(selector: str) -> list:
    css = re.sub(r"/\*.*?\*/", "", CSS.read_text(), flags=re.S)
    out = []
    for sel, body in re.findall(r"([^{}]+)\{([^}]*)\}", css):
        if selector in [s.strip() for s in sel.split(",")]:
            out.append(body)
    return out


def one(selector: str) -> str:
    got = rules(selector)
    assert got, "nothing styles %s" % selector
    return " ".join(got)


def test_it_is_laid_over_the_upper_left_of_the_picture():
    who = one(".photo-frame .who")
    assert re.search(r"position:\s*absolute", who)
    assert re.search(r"(^|[;\s])top:", who) and re.search(r"(^|[;\s])left:", who)
    assert not re.search(r"(^|[;\s])(right|bottom):", who)


def test_the_take_out_button_is_in_the_other_corner():
    cut = one(".cut-dot")
    assert re.search(r"(^|[;\s])right:", cut) and re.search(r"(^|[;\s])bottom:", cut)


def test_it_never_takes_a_click():
    """Information, not a control: a click on it reaches the photograph."""
    assert re.search(r"pointer-events:\s*none", one(".photo-frame .who"))


def test_the_old_line_under_the_caption_is_gone():
    assert not rules(".grid .who"), "the line that pushed the row down is still styled"

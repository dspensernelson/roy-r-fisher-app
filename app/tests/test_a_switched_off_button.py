"""A switched-off button still reads as a button, and as its own button.

Spenser, 2026-09-18, on Build photo pages and Generate captions both off:
*"Everything looks like it's on top of the button, not part of the button."*
The old rule replaced both fills with one flat grey and no edge, so the two
became identical grey slabs that read as words on a box.

What he was given and what this holds: keep the pale fill, and draw an outline
in the button's own colour. Red for the filled red button, blue for the blue
one. It still reads as off, it still reads as a button, and the two stay
distinguishable.
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


def test_off_keeps_the_pale_fill_and_the_quiet_ink():
    off = one(".button.is-off")
    assert "var(--quiet-bg)" in off
    assert "var(--ink-on-quiet)" in off


def test_off_build_is_outlined_in_red():
    assert re.search(r"box-shadow:\s*inset[^;]*var\(--brand\)", one(".button.is-off")), \
        "a switched-off red button has lost its red edge"


def test_off_generate_is_outlined_in_blue():
    assert re.search(r"box-shadow:\s*inset[^;]*var\(--link\)",
                     one(".button.secondary.is-off")), \
        "a switched-off blue button has lost its blue edge"


def test_the_two_off_buttons_do_not_look_the_same():
    red = re.search(r"box-shadow:([^;]*)", one(".button.is-off")).group(1)
    blue = re.search(r"box-shadow:([^;]*)", one(".button.secondary.is-off")).group(1)
    assert red.strip() != blue.strip()


def test_the_outline_does_not_change_the_buttons_size():
    """An inset shadow, not a border. A border would make the button 3px
    taller the moment it switched off, in a widget whose height is pinned."""
    for selector in (".button.is-off", ".button.secondary.is-off"):
        for body in rules(selector):
            assert not re.search(r"(^|[;\s])border(-width)?\s*:", body), \
                "%s changes its border, so it changes size when it switches off" % selector
            assert "padding" not in body


def test_hovering_an_off_button_does_not_light_it_up():
    """`.button.secondary:hover` is written later in the file at the same
    specificity as the old off rule, so hovering a greyed Generate captions
    painted it the live hover blue. The off hover names the secondary
    button itself so it outranks that."""
    assert re.search(r"box-shadow:\s*inset[^;]*var\(--link\)",
                     one(".button.secondary.is-off:hover"))
    assert "var(--quiet-bg)" in one(".button.secondary.is-off:hover")
    assert re.search(r"box-shadow:\s*inset[^;]*var\(--brand\)", one(".button.is-off:hover"))

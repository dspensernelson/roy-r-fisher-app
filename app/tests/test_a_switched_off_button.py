"""A switched-off button is the same button, faded.

Spenser, 2026-09-18, from his check results on 0.7.6.3: *same colour,
faded.* Build photo pages stays red and Generate captions stays blue, faded,
and resting on either still says why it is off.

This replaces the round before it, which kept a pale fill and drew an edge in
the button's own colour. That had answered his earlier complaint about two
identical grey slabs, *"Everything looks like it's on top of the button, not
part of the button."* Same colour, faded, answers both: the two stay two
different buttons, and nothing sits on top of either.

`.is-off` is used on four buttons: Build photo pages (red) and Generate
captions (blue) on the photographs screen, the blue save on Manage active
jobs, and the blue Use this folder on the folder chooser. One rule for all
four.
"""
import re
from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / "web" / "src" / "brand.css"
SCREENS = Path(__file__).resolve().parents[1] / "web" / "src" / "screens"


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


def faded(body: str) -> float:
    m = re.search(r"opacity:\s*([\d.]+)", body)
    assert m, "an off button is not faded"
    return float(m.group(1))


def test_off_build_stays_red_and_fades():
    off = one(".button.is-off")
    assert re.search(r"background:\s*var\(--brand\)", off)
    assert 0.3 <= faded(off) <= 0.6


def test_off_generate_stays_blue_and_fades():
    off = one(".button.secondary.is-off")
    assert re.search(r"background:\s*var\(--link\)", off)
    assert 0.3 <= faded(off) <= 0.6


def test_the_pale_fill_and_the_edge_are_gone():
    for selector in (".button.is-off", ".button.secondary.is-off"):
        body = one(selector)
        assert "var(--quiet-bg)" not in body, "%s is the pale fill again" % selector
        assert "inset" not in body, "%s still draws an edge" % selector


def test_off_does_not_change_the_buttons_size():
    """A widget whose height is pinned cannot have a button that grows when
    it switches off."""
    for selector in (".button.is-off", ".button.secondary.is-off"):
        for body in rules(selector):
            assert not re.search(r"(^|[;\s])border(-width)?\s*:", body)
            assert "padding" not in body


def test_hovering_an_off_button_does_not_light_it_up():
    """`.button:hover` and `.button.secondary:hover` paint the live hover
    colour, so the off hover names each one itself and holds the resting
    colour."""
    assert re.search(r"background:\s*var\(--link\)", one(".button.secondary.is-off:hover"))
    assert re.search(r"background:\s*var\(--brand\)", one(".button.is-off:hover"))


def test_resting_on_an_off_button_still_says_why():
    screen = (SCREENS / "PhotosScreen.jsx").read_text()
    assert 'data-has={buildWhy ? "yes" : "no"}' in screen
    assert 'data-has={generateWhy ? "yes" : "no"}' in screen
    assert re.search(r"\.act-wrap:hover \.why\[data-has=\"yes\"\]", CSS.read_text())

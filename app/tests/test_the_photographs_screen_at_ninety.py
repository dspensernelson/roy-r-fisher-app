"""The photographs screen, at 100 per cent, looks the way it did at 90.

Spenser's checklist: *"The photographs screen must be readable the way it is
at 90 per cent."* He zoomed his browser to 90 per cent to read this screen
comfortably. So the screen's own sizes are scaled by one number, `--k`, set on
the frame only while the photographs screen is in it.

Not by `zoom` and not by a transform on the page: those scale everything
including the app's own bar, and a transform leaves the layout at full size
underneath. Every size on the screen is written as the design number times
`--k`, so the design numbers are still readable in the stylesheet, and every
other screen, where `--k` is not set, falls back to 1 and is untouched.

The real proof is a measurement in a browser, recorded in docs/ROADMAP.md.
These hold the mechanism in place.
"""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web" / "src"
CSS = WEB / "brand.css"
APP = WEB / "App.jsx"


def plain() -> str:
    return re.sub(r"/\*.*?\*/", "", CSS.read_text(), flags=re.S)


def rules(selector: str) -> list:
    out = []
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", plain()):
        if selector in [s.strip() for s in sel.split(",")]:
            out.append(body)
    return out


def scaled(n) -> str:
    return "calc(%spx * var(--k, 1))" % n


def test_the_photographs_frame_carries_the_one_number():
    got = " ".join(rules(".frame.is-photos"))
    assert re.search(r"--k:\s*0\.9\s*;", got), "the photographs screen is not at 90"


def test_only_the_photographs_screen_marks_its_frame():
    app = APP.read_text()
    assert 'view.screen === "photos" ? " is-photos" : ""' in app


def test_nothing_zooms_or_transforms_the_page():
    css = plain()
    assert not re.search(r"(^|[;{\s])zoom\s*:", css), "zoom is not the way"
    assert not re.search(r"(?<![\w-])scale(3d|X|Y)?\(", css), \
        "a transform leaves the layout at full size"


def test_the_widget_is_the_design_number_times_the_scale():
    """360 by 110 is the design. On this screen it now draws 324 by 99."""
    panel = " ".join(rules(".screen-actions.control-panel"))
    assert "width: %s" % scaled(360) in panel
    assert "height: %s" % scaled(110) in panel


def test_the_tiles_and_the_captions_scale():
    assert "minmax(%s, 1fr)" % scaled(200) in " ".join(rules(".grid"))
    assert "font-size: %s" % scaled(14) in " ".join(rules(".grid textarea"))
    assert "width: %s" % scaled(26) in " ".join(rules(".dot"))


def test_the_frame_itself_narrows_with_the_screen():
    """Without this the tiles grow to fill a 1200px frame and are bigger than
    they were at 90 per cent, which is the opposite of the point."""
    frame = " ".join(rules(".frame"))
    assert "max-width: %s" % scaled(1200) in frame


def test_the_app_bar_and_masthead_do_not_scale():
    """They sit outside the frame, on every screen alike."""
    for selector in (".masthead", ".bar-inner", ".wordmark"):
        for body in rules(selector):
            assert "var(--k" not in body, selector

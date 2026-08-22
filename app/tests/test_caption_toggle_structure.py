"""The recommendation flag sits above the option, not inside its label.

What this proves and what it does not. There is no JavaScript test runner in
this project, so these read the screen's own source and the stylesheet and
assert the structure the design system's segmented control specifies:
a separate flag element, before the label, lifted out of the flow and
positioned above the control. That is exactly the defect being guarded
against, which was an <em> sitting inline next to the label.

It does not measure pixels. How it looks is checked by eye on the real app.
"""
import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[1] / "web" / "src"
SCREEN = WEB / "screens" / "PhotosScreen.jsx"
CSS = WEB / "brand.css"
# The design system's own copy of this control, which the app is following.
DESIGN_SYSTEM = (Path(__file__).resolve().parents[2] / "brand" /
                 "Roy R. Fisher Design System" / "components" / "actions" /
                 "SegmentedControl.jsx")
has_design_system = pytest.mark.skipif(
    not DESIGN_SYSTEM.is_file(),
    reason=f"design system not on this machine: {DESIGN_SYSTEM.name}",
)


@pytest.fixture
def toggle_block() -> str:
    """Just the segmented control's markup, from its opening div to its close."""
    text = SCREEN.read_text()
    start = text.index('<div className="toggle">')
    end = text.index("</div>", text.index("</button>", start))
    return text[start:end]


def test_the_flag_is_its_own_element_not_a_word_in_the_label(toggle_block):
    assert 'className="toggle-flag"' in toggle_block
    assert ">suggested<" in toggle_block
    # the shape of the defect: an <em> tucked in beside the label
    assert "<em>" not in toggle_block


def test_the_flag_comes_before_the_label(toggle_block):
    """DOM order first, because the flag is lifted above by position."""
    flag = toggle_block.index("toggle-flag")
    label = toggle_block.index("toggle-label")
    assert flag < label


def test_the_label_is_alone_in_its_element(toggle_block):
    """The option row reads 'View of' and nothing else."""
    match = re.search(r'<span className="toggle-label">\{([^}]+)\}</span>', toggle_block)
    assert match, "the label should be its own span holding only the style's label"
    assert match.group(1).strip() == "s.label"


def test_the_stylesheet_lifts_the_flag_above_the_control():
    css = CSS.read_text()
    block = css[css.index(".toggle-flag {"):]
    block = block[:block.index("}")]
    assert "position: absolute" in block
    assert re.search(r"top:\s*-\d+px", block), "the flag sits above the control, not in it"
    # and the button it hangs off has to be the thing it is positioned against
    button = css[css.index(".toggle button {"):]
    assert "position: relative" in button[:button.index("}")]


def test_the_control_reserves_room_for_the_flag():
    css = CSS.read_text()
    assert ".toggle:has(.toggle-flag)" in css
    block = css[css.index(".toggle:has(.toggle-flag)"):]
    assert re.search(r"margin-top:\s*20px", block[:block.index("}")])


def test_the_flag_is_ruled_the_way_the_design_system_specifies():
    css = CSS.read_text()
    assert ".toggle-flag::before, .toggle-flag::after" in css


@has_design_system
def test_it_follows_the_design_system_rather_than_inventing_a_treatment():
    """The design system says the flag renders above, not as a second word."""
    # collapsed, because the contract is a wrapped comment
    contract = " ".join(DESIGN_SYSTEM.read_text().split())
    assert "renders as a small ruled caption ABOVE the control" in contract
    assert "not as a second word inside the button" in contract


def test_the_recommendation_itself_is_unchanged(toggle_block):
    """Still the job's own caption style, still defaulting to View of."""
    assert 'manifest.caption_style || "view"' in toggle_block

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
    import captions
    assert captions.DEFAULT_STYLE == "view"
    assert captions.STYLES["view"]["label"] == "View of"
    assert captions.STYLES["category"]["label"] == "Location first"

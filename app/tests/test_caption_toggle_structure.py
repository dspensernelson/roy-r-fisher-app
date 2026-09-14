"""The two styles are a plain segmented control. Nothing is recommended at him.

It used to carry a flag reading `suggested` over whichever option the job was
already set to. Spenser, 2026-09-04: *"This view of 'suggested': why the fuck
is it suggested? Who's suggesting it, right? Pull off the suggestion."*
`docs/THE-WALK-2026-09-04.md`, click 8. The word came off on 2026-09-14.

Which style the job starts on has not changed. The control simply shows it the
way a segmented control already shows a selection, by which half is lit, so
nothing had to be said in words.

What this proves and what it does not. These read the screen's own source and
the stylesheet and assert the structure. They do not measure pixels. How it
looks is checked by eye on the real app, and the rendered behaviour is in
`app/web/src/screens/PhotosScreen.test.jsx`.
"""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web" / "src"
SCREEN = WEB / "screens" / "PhotosScreen.jsx"
CSS = WEB / "brand.css"


def toggle_block() -> str:
    """Just the segmented control's markup, from its opening div to its close."""
    text = SCREEN.read_text()
    start = text.index('<div className="toggle">')
    end = text.index("</div>", text.index("</button>", start))
    return text[start:end]


def test_no_option_is_labelled_suggested():
    assert "suggested" not in toggle_block()
    assert "toggle-flag" not in SCREEN.read_text()


def test_the_word_left_no_styling_behind_it():
    """A rule for an element nothing renders is the next session's puzzle."""
    css = CSS.read_text()
    assert "toggle-flag" not in css


def test_the_label_is_alone_in_its_element():
    """The option row reads 'View of' and nothing else."""
    match = re.search(r'<span className="toggle-label">\{([^}]+)\}</span>',
                      toggle_block())
    assert match, "the label should be its own span holding only the style's label"
    assert match.group(1).strip() == "s.label"


def test_the_selection_still_shows_which_style_the_job_is_on():
    """Taking the word off must not take the fact off."""
    block = toggle_block()
    assert 'className={showing === s.key ? "on" : ""}' in block

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
    import captions
    assert captions.DEFAULT_STYLE == "view"
    assert captions.STYLES["view"]["label"] == "View of"
    assert captions.STYLES["category"]["label"] == "Location first"


def test_the_selected_half_is_the_lit_one():
    css = CSS.read_text()
    block = css[css.index(".toggle button.on {"):]
    block = block[:block.index("}")]
    assert "background: #FFFFFF" in block

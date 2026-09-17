"""The update box and the confirm box are not narrow boxes on the left.

Spenser, recorded 2026-09-03 and again on the checklist: *"The update box must
fill the width, not sit in a narrow box on the left."* It was never fixed. A
commit on 2026-09-15 titled "docs: the update box must fill the width" changed
no CSS at all, which is why this is a test and not a commit message.

It had got worse rather than better. `.confirm` capped at 720px and
`.update-step` added a 560px cap on top of it, so by 2026-09-16 the box was
narrower than on the day he complained.

Read as text on purpose. Nothing here renders a browser, so what it can prove
is that the caps are gone and did not come back.
"""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "web" / "src"
CSS = (SRC / "brand.css").read_text(encoding="utf-8")


def _rule(selector: str) -> str:
    at = CSS.index(selector + " {")
    return CSS[at:CSS.index("}", at)]


def test_the_confirm_box_is_not_capped():
    assert "max-width" not in _rule(".confirm")


def test_the_update_box_is_not_capped():
    assert "max-width" not in _rule(".update-step")


def test_the_update_box_still_has_a_rule_of_its_own():
    """If the selector disappears the caps cannot come back through it, but
    neither can anything else, and the next person should find it here."""
    assert ".update-step {" in CSS


def test_the_progress_bar_keeps_its_own_width():
    """Not the same thing. A progress bar stretched across a wide screen reads
    as a page element rather than as a thing that is moving."""
    assert "max-width: 320px" in _rule(".update-bar")


# Text fills the box it sits in. Spenser, 2026-09-17, looking at the update
# box: *"Look how big this box is because you randomly wrap the text
# one-third of the way over."* The box had no cap by then. Its paragraphs
# did: they borrowed `.setting-fine` from the Settings cards, which carried
# `max-width: 62ch`, and so did `.setting-body`. The tests above read only
# the box's own rule, so they passed while the screen was wrong.
#
# A width in `ch`, `em` or `rem` is a measure for words, not for a box. If a
# line is too long to read, the box is too wide: narrow the box, never the
# text. Pixel caps on containers are a different question and are not
# policed here.
TEXT_MEASURE = re.compile(r"\d(?:\.\d+)?\s*(?:ch|r?em)\b")


def _declarations(css: str):
    """Every max-width a rule sets. Media query conditions are not rules and
    are skipped: `@media (max-width: 40em)` narrows nothing."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@media[^{]*\{", "{", css)
    return [m.group(1).strip() for m in
            re.finditer(r"max-(?:width|inline-size)\s*:\s*([^;}]+)", css)]


def test_no_rule_caps_the_width_of_words():
    capped = [v for v in _declarations(CSS) if TEXT_MEASURE.search(v)]
    assert capped == [], "max-width in a text measure: %s" % capped


def test_no_inline_style_caps_the_width_of_words():
    capped = []
    for path in sorted(SRC.rglob("*.js*")):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"maxWidth\s*:\s*([\"'`][^\"'`]*[\"'`])", text):
            if TEXT_MEASURE.search(m.group(1)):
                capped.append("%s: %s" % (path.name, m.group(0)))
    assert capped == [], "inline maxWidth in a text measure: %s" % capped


def test_the_check_would_see_a_text_cap():
    """A check that cannot fail proves nothing. This is the shape that hid
    since the first commit. A comment or a media query is not."""
    assert _declarations(".x { color: red; max-width: 62ch; }") == ["62ch"]
    assert TEXT_MEASURE.search("40em")
    assert not TEXT_MEASURE.search("720px")
    assert _declarations("@media (max-width: 40em) { .x { color: red; } }") == []
    assert _declarations("/* max-width: 62ch */ .x { }") == []

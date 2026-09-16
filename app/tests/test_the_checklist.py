"""The page Spenser works from, held to the rules he set for it.

He does not open markdown. `docs/NOW.md` is the source and the published page
is the only place he sees the state of the project, so every defect in the
build lands on the one surface he reads.

Each rule here was paid for. On 2026-09-15 an item lost its ending because it
wrapped; the same day `B15` reached the page and he said, exactly, that he is
not opening the markdowns and that a bug number means nothing to him. Prose got
onto it twice before that. So: one line per item, no codes, and nothing on the
page that `docs/NOW.md` does not say.

Nothing here reaches the network or publishes anything.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import build_the_checklist as build   # noqa: E402

SOURCE = REPO / "docs" / "NOW.md"


def sections():
    return build.read(SOURCE)


def page():
    return build.build(sections())


# --- the source itself ------------------------------------------------------

def test_every_line_in_the_file_is_a_heading_an_item_or_a_note():
    """A checkbox line that is not recognised silently disappears from the
    page, which is worse than a crash: the item is gone and nobody is told."""
    found = sum(len(items) for _, items in sections())
    raw = sum(1 for line in SOURCE.read_text(encoding="utf-8").splitlines()
              if line.startswith("- ["))
    assert found == raw, "%d checkbox lines in the file, %d reached the page" % (
        raw, found)


def test_no_item_carries_a_code():
    """`B15` reached the page once. He read it and did not know what it was."""
    for heading, items in sections():
        for _, text in items:
            assert not re.search(r"\b[A-Z]\d+\b", text), (
                "%s, under %s, has a code in it" % (text, heading))


def test_every_item_is_one_line():
    for heading, items in sections():
        for _, text in items:
            assert "\n" not in text
            assert len(text) <= build.LONG_ITEM, (
                "%d characters under %s, it will wrap: %s"
                % (len(text), heading, text))


def test_the_north_star_is_first_and_is_his_five():
    """It is the thing every other item is measured against. If it stops being
    first, the page stops being the argument it is meant to be."""
    heading, items = sections()[0]
    assert "north star" in heading.lower()
    assert len(items) == 5


# --- the page ---------------------------------------------------------------

def visible(made):
    """The words a person actually reads. Tags, the stylesheet and the script
    are stripped, because the rule is about what is on the page, not about how
    it is marked up."""
    made = re.sub(r"<(style|script|title)\b.*?</\1>", " ", made, flags=re.S)
    return re.sub(r"<[^>]+>", " ", made)


def test_the_page_says_nothing_the_file_does_not():
    """The build may escape and lay out. It may not add a word. A session
    adding its own wording to his checklist is a recorded fault."""
    words = set(re.findall(r"[A-Za-z]{4,}", visible(page())))
    allowed = set(re.findall(r"[A-Za-z]{4,}", SOURCE.read_text(encoding="utf-8")))
    assert words <= allowed, "the page invented: %s" % sorted(words - allowed)


def test_every_item_reaches_the_page_with_its_state():
    made = page()
    for _, items in sections():
        for done, text in items:
            import html
            assert html.escape(text) in made, "%s is not on the page" % text
    ticked = sum(1 for _, items in sections() for done, _ in items if done)
    assert len(re.findall(r'type="checkbox" id="c\d+" checked>', made)) == ticked


def test_the_first_two_sections_are_open_and_the_rest_fold():
    """He opens the page for the north star and for what stands between him
    and the office. Everything else may be folded away or the page stops
    being readable at a glance."""
    made = page()
    assert made.count("<details") == len(sections())
    assert made.count(" open>") == min(build.ALWAYS_OPEN, len(sections()))


def test_an_item_with_html_in_it_cannot_break_the_page():
    made = build.build([("A heading", [(False, 'a <script>alert(1)</script> item')])])
    assert "<script>alert" not in made
    assert "&lt;script&gt;" in made


def test_the_complaint_is_a_warning_and_never_a_refusal():
    """A build that refuses could stop a session publishing at all, and the
    page being slightly wrong beats the page being absent or stale."""
    import io
    bad = [("A heading", [(False, "B15 " + "x" * 200)])]
    said = build.complain(bad, out=io.StringIO())
    assert len(said) == 2
    assert "<details" in build.build(bad)

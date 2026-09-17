"""The page Spenser works from, held to the rules he set for it.

He does not open markdown. `docs/NOW.md` is the source and the published page
is the only place he sees the state of the project, so every defect in the
build lands on the one surface he reads.

Each rule here was paid for. On 2026-09-15 an item lost its ending because it
wrapped; the same day `B15` reached the page and he said, exactly, that he is
not opening the markdowns and that a bug number means nothing to him. Prose got
onto it twice before that. So: one line per item, no codes, and nothing on the
page that `docs/NOW.md` does not say.

On 2026-09-16 the `Done` heading came out of the file. Every ticked item stays
under the heading it belongs to, and the page gathers them into a `Done`
section it generates itself. The rules that used to be a person's memory are
tested here instead: the file has no `Done` heading, the page has one, it holds
every ticked item and only those, and each of those items is also under its own
heading, hidden until that heading's own line pulls it up.

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
        for _, text, _ in items:
            assert not re.search(r"\b[A-Z]\d+\b", text), (
                "%s, under %s, has a code in it" % (text, heading))


def test_every_item_is_one_line():
    for heading, items in sections():
        for _, text, _ in items:
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


def rows(made):
    """Every item row: (its classes, the rest of its attributes, its words)."""
    return [(m.group(1), m.group(2), m.group(3)) for m in re.finditer(
        r'<label class="(row[^"]*)"([^>]*)>.*?<span class="t">(.*?)</span>',
        made, re.S)]


def section_of(made, heading):
    """The one `details` block under that heading, or None."""
    import html
    for m in re.finditer(r"<details\b.*?</details>", made, re.S):
        got = re.search(r"<summary>(.*?)<span", m.group(0), re.S)
        if got and got.group(1) == html.escape(heading):
            return m.group(0)
    return None


def test_the_page_says_nothing_the_file_does_not():
    """The build may escape and lay out. It may not add a word. A session
    adding its own wording to his checklist is a recorded fault."""
    words = set(re.findall(r"[A-Za-z]{4,}", visible(page())))
    allowed = set(re.findall(r"[A-Za-z]{4,}", SOURCE.read_text(encoding="utf-8")))
    assert words <= allowed, "the page invented: %s" % sorted(words - allowed)


def test_every_item_reaches_the_page_with_its_state():
    made = page()
    for _, items in sections():
        for done, text, _ in items:
            import html
            assert html.escape(text) in made, "%s is not on the page" % text
    ticked = sum(1 for _, items in sections() for done, _, _ in items if done)
    # Twice: once under its own heading and once in the generated Done.
    assert len(re.findall(r'checkbox" data-k="c\d+" checked>', made)) == ticked * 2


def test_the_first_two_sections_are_open_and_the_rest_fold():
    """He opens the page for the north star and for what stands between him
    and the office. Everything else may be folded away or the page stops
    being readable at a glance."""
    made = page()
    assert made.count("<details") == len(sections()) + 1, "the file's headings and the generated Done"
    assert made.count(" open>") == min(build.ALWAYS_OPEN, len(sections()))


def test_an_item_with_html_in_it_cannot_break_the_page():
    made = build.build([("A heading", [(False, 'a <script>alert(1)</script> item', "")])])
    assert "<script>alert" not in made
    assert "&lt;script&gt;" in made


def test_the_complaint_is_a_warning_and_never_a_refusal():
    """A build that refuses could stop a session publishing at all, and the
    page being slightly wrong beats the page being absent or stale."""
    import io
    bad = [("A heading", [(False, "B15 " + "x" * 200, "")])]
    said = build.complain(bad, out=io.StringIO())
    assert len(said) == 2
    assert "<details" in build.build(bad)


# --- the star, put into everything ------------------------------------------

def test_every_item_outside_the_north_star_names_the_star_it_serves():
    """He asked for this on 2026-09-16: the star goes into everything. An item
    with nothing said either way is the failure this catches, because silence
    reads as "nobody thought about it", which is exactly what it is."""
    for heading, items in list(sections())[1:]:
        for _, text, star in items:
            assert star, "%s, under %s, says nothing about the star" % (text, heading)
            assert star == build.NO_STAR or star in build.STARS, (
                "%s is not one of the five and is not %s: %s"
                % (star, build.NO_STAR, text))


def test_the_north_star_itself_carries_no_star():
    """The five are what everything else points at. A line pointing at itself
    is noise."""
    for _, _, star in sections()[0][1]:
        assert not star


def test_the_star_is_beside_the_words_and_never_inside_them():
    """It is laid out, not written into the sentence. If it ever reached the
    text, the item would read as though he had said it."""
    for heading, items in sections():
        for _, text, _ in items:
            assert build.MARK not in text
            assert not text.endswith(build.NO_STAR)


def test_a_star_reaches_the_page_as_its_own_thing():
    made = build.build([("A heading", [(False, "an item", "Star 3"),
                                       (False, "another", build.NO_STAR)])])
    assert '<span class="star">Star 3</span>' in made
    assert '<span class="star none">No star</span>' in made


def test_nothing_appears_under_two_headings():
    """Crossover. He asked for it by name on 2026-09-16. The same work in two
    places is how a thing gets built twice or argued about twice."""
    import io as _io
    said = [one for one in build.complain(sections(), out=_io.StringIO())
            if one.startswith("crossover")]
    assert not said, "\n".join(said)


def test_the_headings_are_his_eight_in_time_order():
    """The order he approved on 2026-09-16: soonest first, the north star at
    the top because everything else is measured against it. He could not tell
    what was next from the headings before these, because they sorted on three
    different questions at once. `Done` is not among them: the page makes it."""
    assert [h for h, _ in sections()] == [
        "The north star",
        "What needs you",
        "Get the office a working update",
        "Description of improvements",
        "The report, section by section",
        "You asked for it and it is not built",
        "Ideas nobody has confirmed with you",
        "Housekeeping",
    ]


# --- Done is generated, not written --------------------------------------

def test_the_file_has_no_done_heading():
    """A person had to remember to move an item to `Done` when they ticked it,
    and nobody is reminded of that rule. The file keeps every item under the
    heading it belongs to, which is the only place that knows where a done
    item came from, and the page gathers them."""
    for heading, _ in sections():
        assert heading != build.DONE, "`%s` is written in the file again" % build.DONE


def test_a_ticked_item_sits_at_the_bottom_of_its_heading():
    """Below the open ones. What is left to do is what he reads first."""
    for heading, items in sections():
        states = [done for done, _, _ in items]
        assert states == sorted(states), (
            "a done item is above an open one under %s" % heading)


def test_the_page_has_a_done_section_holding_every_ticked_item_and_only_those():
    made = page()
    body = section_of(made, build.DONE)
    assert body is not None, "the page has no %s section" % build.DONE
    inside = [text for _, _, text in rows(body)]
    import html
    want = [html.escape(t) for _, items in sections() for d, t, _ in items if d]
    assert inside == want, "%s holds the wrong items" % build.DONE


def test_every_ticked_item_is_also_under_its_own_heading_hidden_on_load():
    """It is not moved. It is in both places, and the heading's own line
    decides which of the two you can see."""
    import html
    made = page()
    for heading, items in sections():
        body = section_of(made, heading)
        put = {text: kind for kind, _, text in rows(body)}
        for done, text, _ in items:
            here = html.escape(text)
            assert here in put, "%s is not under %s" % (text, heading)
            assert (put[here] == "row away") == done, (
                "%s under %s is shown the wrong way round" % (text, heading))


def test_nothing_is_open_in_two_places_when_the_page_loads():
    """A ticked item is on the page twice. Exactly one of the two is in view
    until he asks for the other."""
    made = page()
    shown = [text for kind, _, text in rows(made) if kind == "row"]
    assert len(shown) == len(set(shown)), (
        "in view twice: %s" % sorted(t for t in set(shown) if shown.count(t) > 1))
    assert len(shown) == sum(len(items) for _, items in sections())


def test_a_heading_with_done_items_carries_a_line_saying_how_many():
    """A line, not a button, at the end of the heading. Clicking it pulls that
    heading's done items up out of `Done`."""
    made = page()
    for at, (heading, items) in enumerate(sections()):
        done = sum(1 for d, _, _ in items if d)
        line = '<div class="pull" data-for="%d">%d done</div>' % (at, done)
        assert (line in made) == bool(done), (
            "%s has %d done items and the line does not match" % (heading, done))


def test_the_done_rows_say_which_heading_they_came_from():
    """The file is the only place that knows, so the page has to carry it."""
    made = page()
    body = section_of(made, build.DONE)
    came = [re.search(r'data-from="(\d+)"', attrs).group(1)
            for _, attrs, _ in rows(body)]
    want = [str(at) for at, (_, items) in enumerate(sections())
            for d, _, _ in items if d]
    assert came == want


def test_no_ticked_item_and_no_done_section_when_nothing_is_ticked():
    made = build.build([("A heading", [(False, "an item", build.NO_STAR)])])
    assert build.DONE not in made
    assert made.count("<details") == 1

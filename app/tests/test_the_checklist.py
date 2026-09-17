"""The page Spenser works from, held to the rules he set for it.

He does not open markdown. `docs/NOW.md` is the source and the published page
is the only place he sees the state of the project, so every defect in the
build lands on the one surface he reads.

Each rule here was paid for. On 2026-09-15 an item lost its ending because it
wrapped; the same day `B15` reached the page and he said, exactly, that he is
not opening the markdowns and that a bug number means nothing to him. Prose got
onto it twice before that. So: one line per item, no codes, and nothing on the
page that `docs/NOW.md` does not say.

On 2026-09-17 the north star stopped being one heading holding five lines and
became five headings, each holding the work that moves it. The five lines are
no longer items. An item still names its star after the middle dot, and that
is how it finds its heading; the page stops drawing the star beside the words,
because the heading above them already says it.

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


# His five sentences, in his order, as the checklist words them. Each is a
# heading now, not an item. Written out here rather than read from the build,
# so a change to either one is caught by the other.
NORTH_STAR = [
    "Press Update: the new app opens, the old one closes, nothing else happens",
    "Double-click the icon: it opens, anything else running shuts down",
    "Close the tab, or press Close the app: everything closes",
    "Never shown an old screen or an old message",
    "The app never says anything it does not know",
]


def test_the_north_star_is_first_and_is_his_five_headings():
    """It is the thing every other item is measured against. If it stops being
    first, the page stops being the argument it is meant to be. Since
    2026-09-17 each line is its own heading, so the work that moves a star
    sits under it and the heading shows that star's progress."""
    assert [h for h, _ in sections()][:5] == NORTH_STAR
    assert len(build.STARS) == len(NORTH_STAR)


def test_the_five_lines_are_headings_and_no_longer_items():
    """An item that repeats its own heading is noise, and a line that is both
    would be ticked as though a star were done."""
    for heading, items in sections():
        for _, text, _ in items:
            assert text not in NORTH_STAR, "%s is an item under %s" % (text, heading)


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
    adding its own wording to his checklist is a recorded fault.

    The notes control is furniture and gets the one exception, held to the
    two short lines named in the build and tested below. It never reaches an
    item's words, which the next test holds separately."""
    words = set(re.findall(r"[A-Za-z]{4,}", visible(page())))
    allowed = set(re.findall(r"[A-Za-z]{4,}", SOURCE.read_text(encoding="utf-8")))
    allowed |= build.FURNITURE
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


def test_the_five_stars_and_what_needs_you_are_open_and_the_rest_fold():
    """He opens the page for the north star and for what is waiting on him.
    Everything else may be folded away or the page stops being readable at a
    glance. Six headings, set on 2026-09-17 when the star became five."""
    made = page()
    assert made.count("<details") == len(sections()) + 1, "the file's headings and the generated Done"
    assert build.ALWAYS_OPEN == 6
    assert [h for h, _ in sections()][build.ALWAYS_OPEN - 1] == "What needs you"
    opened = re.findall(r'<details id="s\d+"[^>]* open><summary>(.*?)<span', made)
    assert opened == [h for h, _ in sections()][:build.ALWAYS_OPEN]


def test_an_item_with_html_in_it_cannot_break_the_page():
    made = build.build([("A heading", [(False, 'a <script>alert(1)</script> item', "")])])
    assert "<script>alert" not in made
    assert "&lt;script&gt;" in made


def test_the_complaint_is_a_warning_and_never_a_refusal():
    """A build that refuses could stop a session publishing at all, and the
    page being slightly wrong beats the page being absent or stale."""
    import io
    # Named for the first star, because it is under the first heading and
    # only the code and the length are meant to be wrong with it.
    bad = [("A heading", [(False, "B15 " + "x" * 200, "Star 1")])]
    said = build.complain(bad, out=io.StringIO())
    assert len(said) == 2
    assert "<details" in build.build(bad)


# --- the star, put into everything ------------------------------------------

def test_every_item_names_the_star_it_serves():
    """He asked for this on 2026-09-16: the star goes into everything. An item
    with nothing said either way is the failure this catches, because silence
    reads as "nobody thought about it", which is exactly what it is. Since the
    five lines became headings there is no section exempt from it."""
    for heading, items in sections():
        for _, text, star in items:
            assert star, "%s, under %s, says nothing about the star" % (text, heading)
            assert star == build.NO_STAR or star in build.STARS, (
                "%s is not one of the five and is not %s: %s"
                % (star, build.NO_STAR, text))


def test_every_starred_item_sits_under_its_own_star_open_or_ticked():
    """The suffix is how an item finds its heading. Ticked ones come too, so
    each star shows how far along it is."""
    for at, (heading, items) in enumerate(sections()):
        for _, text, star in items:
            if star in build.STARS:
                assert heading == NORTH_STAR[build.STARS.index(star)], (
                    "%s names %s and sits under %s" % (text, star, heading))


def test_nothing_under_a_star_heading_says_no_star():
    """No star items stay where time order puts them."""
    for heading, items in sections()[:len(NORTH_STAR)]:
        for _, text, star in items:
            assert star in build.STARS, "%s says %s under %s" % (text, star, heading)


def test_the_build_complains_about_an_item_under_the_wrong_star():
    import io
    bad = [(NORTH_STAR[0], [(False, "an item", "Star 2")]),
           (NORTH_STAR[1], [(False, "another", build.NO_STAR)])]
    said = build.complain(bad, out=io.StringIO())
    assert any("an item" in one for one in said)
    assert any("another" in one for one in said)


def test_the_star_is_beside_the_words_and_never_inside_them():
    """It is laid out, not written into the sentence. If it ever reached the
    text, the item would read as though he had said it."""
    for heading, items in sections():
        for _, text, _ in items:
            assert build.MARK not in text
            assert not text.endswith(build.NO_STAR)


def test_the_page_no_longer_draws_the_star_beside_an_item():
    """The heading above the item already says which star it serves, and a
    badge repeating it on every row is the ten words where three will do."""
    made = build.build([("A heading", [(False, "an item", "Star 3"),
                                       (False, "another", build.NO_STAR)])])
    assert 'class="star' not in made
    assert "Star 3" not in visible(made)
    assert build.NO_STAR not in visible(made)
    assert 'class="star' not in page()


def test_the_star_headings_are_marked_as_the_north_star():
    """The north star heading was drawn in the brand colour. All five are now."""
    made = page()
    for at, heading in enumerate(NORTH_STAR):
        assert re.search(r'<details id="s%d" class="north"[^>]*><summary>%s<span'
                         % (at, re.escape(heading)), made), heading
    assert made.count('class="north"') == len(NORTH_STAR)


def test_nothing_appears_under_two_headings():
    """Crossover. He asked for it by name on 2026-09-16. The same work in two
    places is how a thing gets built twice or argued about twice."""
    import io as _io
    said = [one for one in build.complain(sections(), out=_io.StringIO())
            if one.startswith("crossover")]
    assert not said, "\n".join(said)


def test_the_headings_are_his_five_stars_then_his_seven_in_time_order():
    """The order he approved on 2026-09-16: soonest first, the north star at
    the top because everything else is measured against it. He could not tell
    what was next from the headings before these, because they sorted on three
    different questions at once. On 2026-09-17 the one north star heading
    became five. `Done` is not among them: the page makes it."""
    assert [h for h, _ in sections()] == NORTH_STAR + [
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


# --- the notes control ------------------------------------------------------
#
# He asked for it on 2026-09-16: "now there needs to be a notes button to the
# left of the star. When i click it leave notes i can hand to you". The note
# goes to the artifact's own store when the page is published, and to this
# browser when it is opened as a file on his Mac, which is what he does. The
# rules below are the ones that can quietly break without anybody noticing.


def labels(made):
    """Every item row, whole."""
    return re.findall(r'<label class="row[^"]*"[^>]*>.*?</label>', made, re.S)


def script(made):
    got = re.search(r"<script>(.*?)</script>", made, re.S)
    assert got, "the page has no script"
    return got.group(1)


def test_the_page_holds_every_item_and_every_tick_the_file_has():
    """The count before and after, in one place. A ticked item is written
    twice, so the rows are the items plus the ticks."""
    made = page()
    raw = SOURCE.read_text(encoding="utf-8").splitlines()
    items = sum(1 for line in raw if line.startswith("- ["))
    ticks = sum(1 for line in raw if line.startswith("- [x]"))
    assert len(labels(made)) == items + ticks
    assert made.count('class="note"') == items + ticks


def test_every_row_carries_a_notes_control_after_the_words():
    """His words were left of the star, on every row, ticked or not. The star
    is no longer drawn, so the control is the last thing on the row, where
    the star's left edge used to be."""
    for one in labels(page()):
        at = one.find('<button type="button" class="note"')
        assert at > 0, "a row has no notes control: %s" % one
        assert at > one.index('<span class="t">'), "it is before the words"
        assert one.index("</button>") == len(one) - len("</button></label>")


def note_keys(made):
    return re.findall(r'class="note" data-n="([^"]+)"', made)


def key_for(made, text):
    """The note key beside one item's words."""
    import html
    got = re.search(
        r'<span class="t">%s</span><button type="button" class="note" data-n="([^"]+)"'
        % re.escape(html.escape(text)), made)
    assert got, "no notes control beside %s" % text
    return got.group(1)


def test_a_note_is_keyed_on_the_items_own_words_and_nothing_else():
    """The words are what the note is about. Where the item sits, which
    heading it is under, which star it names and whether it is ticked all
    change while the item stays the same thing."""
    here = build.build([("A heading", [(False, "the item with the note", "Star 1")])])
    there = build.build([("Another heading",
                          [(True, "the item with the note", build.NO_STAR)])])
    assert key_for(here, "the item with the note") == key_for(
        there, "the item with the note")


def test_a_note_follows_its_item_to_a_different_heading():
    """Items moved between headings four times on 2026-09-16 and will again.
    A note keyed on where an item sat would land on a stranger."""
    before = build.build([("Get the office a working update",
                           [(False, "the item with the note", build.NO_STAR)])])
    after = build.build([("A heading", [(False, "something else", build.NO_STAR)]),
                         ("Housekeeping",
                          [(False, "the item with the note", build.NO_STAR)])])
    assert key_for(before, "the item with the note") == key_for(
        after, "the item with the note")


def test_a_note_follows_its_item_when_items_are_added_above_it():
    """Items are added to `docs/NOW.md` the moment he asks for something, and
    they are added wherever they belong, not at the bottom."""
    before = build.build([("A heading",
                           [(False, "the item with the note", build.NO_STAR)])])
    after = build.build([("A heading", [(False, "one added above", build.NO_STAR),
                                        (False, "and another", build.NO_STAR),
                                        (False, "the item with the note",
                                         build.NO_STAR)])])
    assert key_for(before, "the item with the note") == key_for(
        after, "the item with the note")
    # And the tick's own key does move, which is exactly why the note may not
    # borrow it.
    assert re.search(r'data-k="c1"', before)
    assert 'data-k="c3"' in after


def test_rewording_an_item_orphans_its_note():
    """Correct, and better than the note quietly landing on a stranger. The
    note keeps the item's whole line, which is how an orphan is found."""
    before = build.build([("A heading", [(False, "the item", build.NO_STAR)])])
    after = build.build([("A heading", [(False, "the item, reworded", build.NO_STAR)])])
    assert key_for(before, "the item") != key_for(after, "the item, reworded")


def test_the_note_key_is_never_the_tick_key():
    """Two keys doing two jobs. The tick's counts down the page and moves
    when anything above it moves; the note's is the item's own words."""
    for one in labels(page()):
        assert re.search(r'data-k="c\d+"', one)
        assert not re.search(r'class="note" data-n="c\d+"', one)


def test_every_item_has_its_own_note_key():
    """No two items share one. The file already forbids two items with the
    same words; this is the other half of that."""
    keys = set(note_keys(page()))
    texts = set(t for _, items in sections() for _, t, _ in items)
    assert len(keys) == len(texts)


def test_a_note_key_is_a_legal_place_to_put_a_document():
    """The store takes letters, digits and a short list of marks, and never a
    bare dot. A key it refuses loses the note with no way to see why."""
    for k in set(note_keys(page())):
        assert re.match(r"^[A-Za-z0-9_.~:@+-]{1,200}$", k), k
        assert k not in (".", "..")


def test_both_copies_of_a_ticked_item_share_one_note():
    """A ticked item is on the page twice. One note, not two. Same words,
    same key, so it falls out rather than being arranged."""
    made = page()
    keys = note_keys(made)
    ticks = sum(1 for _, items in sections() for d, _, _ in items if d)
    assert len(keys) - len(set(keys)) == ticks


def test_a_row_carries_its_heading_and_its_star_for_the_note_to_record():
    """A note has to say which heading and which star its item sat under, or
    it is a sentence about nothing when it is read back."""
    import html
    made = page()
    for heading, items in sections():
        for _, text, star in items:
            for one in labels(made):
                if '<span class="t">%s</span>' % html.escape(text) not in one:
                    continue
                assert 'data-h="%s"' % html.escape(heading) in one, text
                assert 'data-s="%s"' % html.escape(star) in one, text


def test_the_notes_control_adds_no_word_to_any_item():
    """The rule that the build never adds a word to an item still stands.
    The control is furniture beside the words, never inside them."""
    import html
    made = page()
    said = re.findall(r'<span class="t">(.*?)</span>', made, re.S)
    want = [html.escape(t) for _, items in sections() for _, t, _ in items]
    ticked = [html.escape(t) for _, items in sections() for d, t, _ in items if d]
    assert sorted(said) == sorted(want + ticked)


def test_the_two_things_the_notes_control_says_are_named_and_no_more():
    """The exception to "the page says nothing the file does not" is exactly
    this and it is written down. If it grows, this test says so."""
    assert build.KEPT_HERE == "This browser only"
    assert build.NOT_KEPT == "Not saved"
    assert build.FURNITURE == {"This", "browser", "only", "saved"}
    made = page()
    assert made.count(build.KEPT_HERE) == 1
    assert made.count(build.NOT_KEPT) == 1


def test_the_page_says_it_is_this_browser_only_when_there_is_no_database():
    """The store is not there when he opens the file on his Mac, which is
    what he does. The page has to work and it has to say where the note
    went. Never show a note as saved when it is not."""
    made = page()
    assert build.KEPT_HERE in visible(made), "the page never says it"
    body = re.search(r'<div class="box".*?</div>\s*</div>', made, re.S).group(0)
    assert build.KEPT_HERE in body and build.NOT_KEPT in body
    s = script(made)
    assert "localStorage" in s, "there is no fallback store"
    assert "rrf-notes" in s, "the notes would land on the tick's own key"


def test_the_notes_box_says_nothing_until_it_has_something_to_say():
    """Both lines start hidden. A page that opens already claiming something
    about a store it has not reached yet is the fifth north-star line."""
    made = page()
    for one in re.findall(r'<span class="say[^"]*"[^>]*>', made):
        assert " hidden>" in one, one


def test_the_page_never_writes_on_a_keystroke():
    """Recorded fault. A caption box wrote on every keystroke and that was
    one read across the office network per letter Colleen typed."""
    made = page()
    s = script(made)
    assert not re.search(r"addEventListener\(\s*['\"]input['\"]", s), (
        "something is bound to every keystroke")
    assert "oninput" not in made
    # And the other half: even when he has finished, nothing is written
    # unless the words are different from the ones already held.
    assert re.search(r"===\s*was\s*\)\s*return", s), (
        "a write can happen when the note has not changed")


def test_every_touch_of_browser_storage_is_wrapped():
    """It throws outright in some contexts, and an unwrapped read takes the
    whole page down with it."""
    s = script(page())
    for got in re.finditer(r"localStorage", s):
        before = s[:got.start()]
        assert before.count("try{") > before.count("}catch"), (
            "a localStorage call sits outside a try")


def test_the_page_does_not_wait_on_the_database_to_draw():
    """It can take ten seconds and it can answer after the page is built.
    The page draws, then the notes light up."""
    s = script(page())
    assert "claude" in s, "the store is never asked for"
    assert re.search(r"window\.claude", s), "it is not guarded"
    assert "await" not in s, "the page waits on the store"
    assert re.search(r"\.then\(", s), "nothing handles the answer later"


def test_a_row_holding_a_note_looks_different_from_one_that_does_not():
    """He has to see at a glance where he left notes, without a word being
    added to say so."""
    made = page()
    assert ".note{" in made
    assert ".note.on{" in made


def test_the_notes_control_cannot_tick_the_item():
    """It sits inside the row's label. A control that ticks the box when he
    reaches for a note is the caption the tick ate, again."""
    made = page()
    assert made.count('<button type="button" class="note"') == made.count('class="note"')
    assert "preventDefault" in script(made)


def test_a_note_never_changes_the_item_it_is_about():
    """Words, star, tick and heading are the file's, not the control's."""
    made = build.build([("A heading", [(False, "an item", "Star 3"),
                                       (True, "a done one", build.NO_STAR)])])
    assert '<span class="t">an item</span>' in made
    assert 'data-s="Star 3"' in made
    assert 'data-s="No star"' in made
    assert made.count('data-k="c2" checked') == 2

"""The three screen faults Mark named while testing 0.7.0 on Windows.

What this proves and what it does not. These read the stylesheet and the
screen's own source and assert the rules are there. They do not measure
pixels; how it looks is checked by eye on the real app. What they guard is
that the rule exists at all, because each of these three was a missing rule
rather than a wrong value.
"""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web" / "src"
CSS = WEB / "brand.css"
APP = WEB / "App.jsx"


def block(name: str) -> str:
    """One rule's declarations, by its selector."""
    # The photographs screen writes every size as its design number times
    # `--k` (see test_the_photographs_screen_at_ninety.py). These tests are
    # about the design numbers, so they read them with the scale taken off.
    css = re.sub(r"calc\((\d+(?:\.\d+)?px) \* var\(--k, 1\)\)", r"\1", CSS.read_text())
    start = css.index(name + " {")
    return css[start:css.index("}", start)]


# Settings drew five white cards with no space between them, so their borders
# touched and the screen read as one grey slab of text.

def test_a_settings_card_has_room_under_it():
    got = re.search(r"margin-bottom:\s*(\d+)px", block(".setting"))
    assert got, "the settings card needs a bottom margin or the cards touch"
    assert 12 <= int(got.group(1)) <= 24


def test_only_settings_uses_that_card():
    """So giving it a margin cannot open a gap on a screen nobody asked about."""
    users = [p for p in (WEB / "screens").glob("*.jsx")
             if "className=\"setting\"" in p.read_text() and ".test." not in p.name]
    assert [p.name for p in users] == ["Settings.jsx"]


# The dark bar carries the only way out of a job, and it scrolled away with
# the page. Thirty photographs is several screens tall.

def test_the_bar_stays_at_the_top_of_the_window():
    bar = block(".bar")
    assert "position: sticky" in bar
    assert re.search(r"top:\s*0", bar)
    assert re.search(r"z-index:\s*(\d+)", bar), "it has to sit over the page it covers"


def test_the_list_search_row_parks_under_the_bar_rather_than_behind_it():
    """The only other thing in the app that sticks to top: 0."""
    css = CSS.read_text()
    assert ":has(.bar) .picker-head" in css
    parked = block("body:has(.bar) .picker-head")
    assert "var(--bar-height)" in parked
    assert re.search(r"--bar-height:\s*\d+px", css), "one place for the bar's height"


# "we need to make it obvious these are not computer people." The job's own
# name was plain white text that only underlined on hover.

def test_both_ways_out_of_a_job_are_drawn_as_chips():
    chip = block(".bar-inner .crumb-chip")
    assert "border:" in chip
    assert "border-radius:" in chip
    app = APP.read_text()
    assert app.count('"crumb-chip"') == 2, "the way back to Jobs and to the job"
    assert "crumb-back" not in app and "crumb-back" not in CSS.read_text()


# The crumb row grew a second chip on 2026-09-14 and the misalignment showed:
# two bordered chips, two separators and a plain last word, none of them
# sharing a line. Mark saw it on every screen, because the bar is on every
# screen.

def test_the_whole_crumb_row_sits_on_one_line():
    bar = block(".bar-inner")
    assert re.search(r"align-items:\s*center", bar), \
        "stretch put the plain crumbs at the top of the chips' height"
    row = block(".bar-inner > *")
    assert re.search(r"line-height:\s*[\d.]+", row), \
        "chips, separators and the last crumb share one line-height"


# "I want this to be more of a control panel, right? like a rounded panel that
# has controls in it." The buttons and the two switches sat loose on the page.

def test_the_actions_and_the_switches_sit_in_one_panel():
    panel = block(".screen-actions.control-panel")
    assert "var(--paper)" in panel, "white: the only surface allowed on the page"
    assert re.search(r"border-radius:\s*\d+px", panel)
    assert re.search(r"padding:\s*", panel)
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert '"screen-actions control-panel"' in screen


def test_a_switch_that_can_be_undone_carries_no_red_fill():
    """The colour law of 2026-09-08, in docs/ROADMAP.md.

    A red fill means a control that cannot be taken back, one per screen at
    most. Bands and Per page are completely undoable and were the loudest
    things on the photographs screen.

    Superseded on 2026-09-15 by the approved design, as to which controls
    these are. They were two identical pills, which is the other half of the
    complaint: two controls doing different jobs must not look the same. Bands
    is on or off, so it is a switch; Per page is a value, so it is a track of
    values. The colour rule is unchanged and now reads off both of them.
    """
    lit = block(".values button.on")
    assert "var(--brand)" not in lit, "a red fill is reserved for the one-way control"
    assert "background:" in lit, "it still has to read as the chosen half"
    assert "var(--paper)" in lit
    track = block(".values")
    assert "var(--paper-sunk)" in track, "the track is sunk so the lit half reads as raised"
    on = block('.switch[aria-checked="true"]')
    assert "var(--brand)" not in on, "the switch is undoable too"


def test_the_two_settings_do_not_look_like_each_other():
    """Spenser's theory, approved 2026-09-14: two controls doing different
    jobs do not look the same. Today they were identical pills, which is why
    they read as noise rather than as two different questions."""
    screen = (WEB / "screens" / "PhotosScreen.jsx").read_text()
    assert 'className="switch" role="switch"' in screen, "bands is on or off"
    assert 'className="values" role="group" aria-label="Photographs to a page"' in screen
    assert "bands-pill" not in screen and "pill-opt" not in screen
    css = CSS.read_text()
    assert ".bands-pill" not in css, "a rule for an element nothing renders is a puzzle"
    assert ".pill-opt" not in css


# Click 11 of the walk of 2026-09-04, and asked again on 2026-09-15 looking at
# the shipped screen: *"why does the setting screen still look like 5 panesl
# down instead of 1 | 2 / 3 | 4 / 5 | 6"*. His original words were about
# layout and were written into the roadmap as a complaint about red buttons,
# which is recorded in docs/THE-WALK-2026-09-04.md. The layout never changed.

SETTINGS = WEB / "screens" / "Settings.jsx"


def without_comments(source):
    """What is on the screen, with the notes about why stripped out. A phrase
    deleted from a screen usually survives in the comment explaining that it
    was deleted, and a test that cannot tell the two apart fails on the
    record rather than on the screen."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"^\s*//.*$", "", source, flags=re.M)


def test_settings_is_two_columns():
    grid = block(".settings-grid")
    got = re.search(r"grid-template-columns:\s*([^;]+);", grid)
    assert got, "the cards have to be laid out in columns, not stacked"
    assert len(got.group(1).split()) == 2, "two columns, not one and not three"


def test_the_two_columns_become_one_when_the_window_is_narrow():
    css = CSS.read_text()
    got = re.search(r"@media \(max-width: (\d+)px\) \{ \.settings-grid[^}]*\}", css)
    assert got, "below some width the two columns have to become one"
    assert "grid-template-columns: 1fr" in got.group(0)


def test_the_settings_screen_renders_that_grid():
    screen = SETTINGS.read_text()
    assert '"settings-grid"' in screen
    assert screen.count('"settings-col"') == 2, "one element per column"


def test_the_cards_sit_in_the_order_he_chose():
    """Superseded on 2026-09-15 by the approved design. This test used to say
    the key card comes first, because it is the only card that changes what
    the app can do. He picked the order card by card on the mockup and put the
    key card last. An earlier review argued for first. He decided otherwise
    and that is settled. `Close the app` is not here at all: F13 moved it into
    the nav bar."""
    heads = re.findall(r"<h2>([^<]+)</h2>", SETTINGS.read_text())
    assert heads == [
        "The version you are running",   # left column
        "Where your jobs live",
        "What the app has done",         # right column
        "Your Anthropic key",
    ], heads


def test_no_setting_name_from_the_code_shows_through():
    """*"This is set by RRF_JOBS_HOME on this computer, which overrides the
    saved choice"* is a line of code on a screen he reads."""
    screen = SETTINGS.read_text()
    assert "RRF_JOBS_HOME" not in screen
    assert "overrides the saved choice" not in screen


def test_the_reassurance_paragraph_is_folded_away():
    """Superseded on 2026-09-15 by the approved design. It used to fold two
    paragraphs away. *"Things should be hidden more too."* still holds for
    where the key file is kept. The other one, `What is in it`, is deleted
    rather than folded: Spenser, 2026-09-15, *"what does this actually
    show?"*. It described the log, and the button beside it shows the log, so
    the thing beat the description of the thing."""
    screen = SETTINGS.read_text()
    assert "Where the key is kept" in screen
    assert "showsKeyHome" in screen
    # Off the screen, not merely out of the comment that records why.
    assert "What is in it" not in without_comments(screen)
    assert "showsLogWhat" not in screen


# The widget on the photographs screen, seen on Windows 2026-09-15: *"Look how
# tight that little icon in the upper right is."* Its contents sat 9px from
# its walls, which on Windows metrics is the whole of the room it had.

def test_the_widget_gives_its_contents_room_at_the_sides():
    panel = block(".screen-actions.control-panel")
    got = re.search(r"padding:\s*(\d+)px (\d+)px", panel)
    assert got, "the panel needs a padding it can be measured by"
    assert int(got.group(2)) >= 12, "9px is what he was looking at"


def test_the_widget_keeps_the_fixed_height_that_stops_the_screen_bouncing():
    """The number changed on 2026-09-16 and the property did not.

    It was 76 by 516 and it is 110 by 360, because he moved the pieces
    himself and a bar was added along the bottom. What matters here is not
    either number: it is that both are pinned, so nothing inside this box can
    push the photographs down the screen. A `min-height` would not do, which
    is why this insists on `height`.
    """
    panel = block(".screen-actions.control-panel")
    assert re.search(r"[^-]height:\s*\d+px", panel), "its height is not pinned"
    assert re.search(r"[^-]width:\s*\d+px", panel), "its width is not pinned"


# Spenser's checklist, 2026-09-17, in capitals: the first row of photographs
# covered the bottom of the widget. The widget went from 76px to 110px tall
# on 2026-09-16 and the header that holds it stayed pinned at 76px, so the
# widget's bottom 34px hung out of the header and the photographs, which sit
# 12px under the header, painted over 22px of it, bar and all.

def test_the_header_is_never_shorter_than_the_widget_it_holds():
    """Measured in the running app on 2026-09-17 before this was fixed: header
    76px, widget 110px, first photograph starting 22px above the widget's
    bottom edge, at the top of the page and scrolled, bands on and off.

    `docs/design/photos-widget.html` gives the header `min-height: 76px`, a
    floor, so it grows to whatever the widget is. That cannot bring back the
    bouncing the 76px pin was for: the widget's own height is pinned (the
    test above), so the header is the same height in every state.
    """
    widget = int(re.search(r"[^-]height:\s*(\d+)px",
                           block(".screen-actions.control-panel")).group(1))
    head = block(".screen-head")
    pinned = re.search(r"[^-]height:\s*(\d+)px", head)
    assert not pinned or int(pinned.group(1)) >= widget, \
        "the header is pinned shorter than the widget, so the photographs cover it"
    assert "max-height" not in head, "a ceiling would cut the widget off the same way"
    assert re.search(r"min-height:\s*\d+px", head), "the design gives the header a floor"


def test_the_folder_question_takes_no_floor_from_the_header():
    """The folder question uses the same header with one line of words under
    the title, 71px tall. It never held the widget, so the 76px floor would
    only move the question down."""
    assert re.search(r"min-height:\s*0", block(".screen-head.is-asking"))


def test_the_money_holds_the_right_edge_of_the_bar():
    """Two rules do it, and both were wrong once on 2026-09-16.

    `.money` takes `margin-left: auto` unconditionally. It was written as
    `:first-of-type`, which matches on element type rather than class, so it
    never fired whenever a pill came before the money, which is every state
    but one.

    Clear captions overrides it, so the pair travel right together with a
    fixed gap between them. That override has to outrank
    `.screen-actions.control-panel .linky { margin-left: 0 }`, which is three
    classes; scoped to the panel it does, and unscoped it silently did
    nothing and left the money 91px short of the edge.
    """
    money = block(".money")
    assert re.search(r"margin-left:\s*auto", money), "the money does not hold the edge"

    css = CSS.read_text()
    # The selector, not the word. The rule's own comment names it, which is
    # the point of the comment, so asking whether the words appear anywhere
    # would fail on the explanation rather than on the mistake.
    assert ".money:first-of-type" not in css, "that selector matches on type, not class"
    assert ".control-panel .barline .clear + .money { margin-left: 0; }" in css, \
        "Clear captions no longer pushes the pair right as one"


# The reviewed pill, from 0.7.6.3 on Spenser's virtual machine, 2026-09-18.
# A tick on that pill means one thing, everything is reviewed, and done is not
# a solid dark green: "I don't like the dark green."

def test_the_tick_green_is_one_token():
    """The light green he chose for every tick on 2026-09-17, in the
    Description of Improvements drawing (`--tick` there). Written once, in the
    root, and pointed at from everywhere else. A shade darker from
    2026-09-18, #3A8F52 to #2E7242, so it reads as small text on its tint:
    `test_the_tick_green.py` measures that."""
    css = CSS.read_text()
    assert len(re.findall(r"--tick:\s*#2E7242;", css)) == 1
    assert css.count("#2E7242") == 1, "the tick green is written out a second time"


def test_done_is_the_pale_tint_and_not_a_dark_fill():
    done = block(".pill.done")
    assert "var(--tick)" in done
    assert "#2F5D33" not in done, "done is the dark green he does not like"
    assert "#FFFFFF" not in done, "white on a fill is the solid pill again"


def test_the_done_pill_sits_in_the_bar():
    """`.done` is also the app's old finished-message box, and its 18px top
    margin reached the pill through the shared class name. The done pill hung
    6.7px below the bar in 0.7.6.3, measured in a browser on 2026-09-18. The
    pill's own rule takes the margin back off."""
    assert re.search(r"margin:\s*0", block(".pill.done"))


def test_the_offer_to_tick_all_is_amber_and_not_green():
    """The offer wore the money's green and a tick, and read as done."""
    offer = block(".pill.act")
    assert "47, 93, 51" not in offer and "#2F5D33" not in offer
    hover = block(".pill.act:hover")
    assert "138, 82, 0" in hover, "the hover leaves the amber family"

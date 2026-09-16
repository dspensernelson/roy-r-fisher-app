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
    css = CSS.read_text()
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

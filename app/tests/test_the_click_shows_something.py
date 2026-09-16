"""Double-clicking the icon has to show something straight away.

Before this, the app hashed every file in the package, imported uvicorn, and
waited for the server to answer, all with nothing on screen. Spenser on
2026-09-04, after clicking the icon and seeing nothing: *"the app opened once
but I can't get it to open again"*, and then a moment later, *"wait, it
worked."* He had clicked twice because the first click looked like it failed.

What is tested here is the promise, not the pixels: a page exists, it names the
version, it watches the right port, it moves itself over rather than opening a
second tab, and failing to draw it never stops the app.
"""
import re
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))
sys.path.insert(0, str(APP))

import splash  # noqa: E402


def test_it_names_the_version_he_is_starting(tmp_path):
    page = splash.page(51234, "0.6.8")
    assert "0.6.8" in page
    assert "ROY R. FISHER" in page


def test_it_watches_the_port_the_app_will_answer_on():
    page = splash.page(51234, "0.6.8")
    assert "http://127.0.0.1:51234/" in page


def test_it_replaces_itself_rather_than_opening_a_second_tab():
    """Two tabs is the two-icons fault wearing different clothes."""
    page = splash.page(51234, "0.6.8")
    assert "location.replace" in page
    assert "window.open" not in page


# Superseded on 2026-09-14 by what happened on the Windows machine. This used
# to require the page to say "It has not started" when it gave up. On Edge the
# page could not reach the app at all, so it said that while the app was
# running perfectly well behind it, and it said it after 150 seconds of
# watching a sweeping bar. What it gives up into is now a pointer to the other
# tab, and the wait is short.
def test_it_gives_up_and_says_so_rather_than_spinning_for_ever():
    page = splash.page(51234, "0.6.8")
    assert "is-late" in page
    assert str(splash.GIVE_UP_SECONDS) in page


def test_it_gives_up_quickly_rather_than_after_two_and_a_half_minutes():
    """150 seconds is a long time to sit in front of a sentence that is wrong.

    The app itself waits 30 seconds for its own server to answer, and the
    browser is now opened on the app the moment it does, so nothing is lost by
    this page stepping aside early.
    """
    assert 0 < splash.GIVE_UP_SECONDS <= 30


def test_giving_up_never_claims_the_app_did_not_start():
    """On the Windows machine the app was running and the page said it was not.

    A page loaded from a file on disk may be blocked from asking a server on
    the same computer anything at all, which is indistinguishable from the app
    being dead. So this page may not say which it was.
    """
    page = splash.page(51234, "0.6.8").lower()
    late = page[page.index('class="late"'):]
    for lie in ("has not started", "did not start", "failed to start",
                "could not start", "something went wrong"):
        assert lie not in late, lie


def test_giving_up_points_at_the_tab_the_app_opened_for_itself():
    page = splash.page(51234, "0.6.8").lower()
    late = page[page.index('class="late"'):]
    assert "another tab" in late or "other tab" in late


def test_it_keeps_looking_even_after_it_has_given_up():
    """Giving up changes what it says, not what it is doing. If the app does
    answer later, this page still hands over rather than sitting there."""
    page = splash.page(51234, "0.6.8")
    script = page[page.index("<script>"):]
    said_late = script.index("is-late")
    assert "return" not in script[said_late:script.index("\n", said_late)], \
        "it stops watching the moment it gives up"


def test_it_asks_for_nothing_off_this_machine():
    """It has to render before anything is served, on a machine that may have
    no internet at all."""
    page = splash.page(51234, "0.6.8")
    for reach in ("http://fonts.", "https://", "//cdn", ".woff", "<img"):
        assert reach not in page, reach


def test_it_draws_the_real_mark_and_not_three_plain_bars():
    page = splash.page(51234, "0.6.8")
    assert "polygon" in page
    assert "#8C0C04" in page
    assert "#782028" not in page


def test_it_writes_beside_the_app_and_never_into_a_job(tmp_path):
    path = splash.write(51234, "0.6.8", where=tmp_path)
    assert path.parent == tmp_path
    assert path.name == "starting.html"
    assert "0.6.8" in path.read_text(encoding="utf-8")
    assert not list(tmp_path.glob("*.writing")), "it left its temp file behind"


def test_failing_to_draw_it_never_stops_the_app(monkeypatch):
    """A splash screen is a courtesy. It may not become a reason not to start."""
    def cannot(_port, _version, where=None):
        raise OSError("this disk is full")

    monkeypatch.setattr(splash, "write", cannot)
    assert splash.show(51234, "0.6.8", opener=lambda _u: True) is False


def test_a_browser_that_refuses_is_not_an_error():
    assert splash.show(51234, "0.6.8", opener=lambda _u: False) is False


def test_it_opens_a_file_on_this_machine(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(splash, "splash_dir", lambda: tmp_path)
    assert splash.show(51234, "0.6.8", opener=lambda u: seen.append(u) or True)
    assert seen[0].startswith("file://")
    assert seen[0].endswith("starting.html")


# --- saying what is actually happening --------------------------------------
# Added 0.7.1. When a copy is already running, the first thing the app does is
# stop it, and that takes a few seconds in which nothing else is on screen.

def test_by_default_it_says_the_app_is_starting():
    assert "Starting version 0.6.8" in splash.page(51234, "0.6.8")


def test_it_can_say_what_is_happening_instead():
    page = splash.page(51234, "0.6.8", saying="Closing the copy that is already open.")
    assert "Closing the copy that is already open." in page
    assert "Starting version 0.6.8. This takes" not in page


def test_it_can_be_told_to_wait_longer_before_giving_up():
    """Stopping the old copy is a legitimate wait. Saying "look in another tab"
    in the middle of it would point him at the copy being closed."""
    page = splash.page(51234, "0.6.8", patience=90)
    assert "90 * 1000" in page


def test_the_launcher_draws_one_screen_that_says_which_case_it_is():
    source = (APP / "run_app.py").read_text(encoding="utf-8")
    assert "splash.show(\n        port, version, saying=" in source


# --- the order in run_app, which is the whole point ------------------------
def test_the_screen_goes_up_before_the_package_check():
    """A loading screen after the slow work is not a loading screen.

    Asserted on the source, because the thing being tested is an order, and
    the slow part is a real package that is not present in a checkout.
    """
    source = (APP / "run_app.py").read_text(encoding="utf-8")
    shows = source.index("splash.show(")
    checks = source.index("packaging.verify(ROOT)")
    assert shows < checks, "the screen goes up after the hashing, which shows nothing"


def test_the_port_is_known_before_the_screen_is_drawn():
    source = (APP / "run_app.py").read_text(encoding="utf-8")
    assert source.index("startup.pick_a_port()") < source.index("splash.show(")


def test_the_record_of_a_running_app_is_still_written_after_the_check():
    """Moving the check must not have moved this. Writing it before the check
    would mean writing into a package that has not been verified."""
    source = (APP / "run_app.py").read_text(encoding="utf-8")
    assert source.index("packaging.verify(ROOT)") < source.index("startup.write_runtime(")


# Rewritten twice, and both times by his machine.
#
# It first required that the browser was NOT opened when the loading page had
# been drawn, so as to avoid a second tab. On 2026-09-14 Edge blocked that page
# from reaching the app, the handover never happened, and the app was left
# running with nobody looking at it, so the open was made unconditional and
# this test required that.
#
# Now the page says when it arrives, so the launcher can tell the two apart.
# What is required here is the half that must never be lost: nothing arriving
# still opens the app. `test_one_tab_not_two.py` holds the rest.
def test_the_app_is_opened_when_the_loading_page_never_reached_it():
    source = (APP / "run_app.py").read_text(encoding="utf-8")
    body = source[source.index("def when_up():"):source.index("def tidy_cache():")]
    assert "webbrowser.open(" in body, "nothing opens the app once it answers"
    opens = body.index("webbrowser.open(")
    guard = body.rindex("if ", 0, opens)
    assert "not" in body[guard:opens], \
        "the browser is opened on a message, rather than on the lack of one"


def test_the_splash_ships_inside_the_package():
    """It runs before uvicorn is imported, so it has to be there in a package
    whose wheels are the thing that went missing."""
    source = (APP / "server" / "splash.py").read_text(encoding="utf-8")
    for third_party in ("import fastapi", "import uvicorn", "import anthropic", "import PIL"):
        assert third_party not in source, third_party

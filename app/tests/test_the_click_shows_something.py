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


def test_it_gives_up_and_says_so_rather_than_spinning_for_ever():
    page = splash.page(51234, "0.6.8")
    assert "is-late" in page
    assert "It has not started" in page
    assert str(splash.GIVE_UP_SECONDS) in page


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
    assert source.index("startup.free_port()") < source.index("splash.show(")


def test_the_record_of_a_running_app_is_still_written_after_the_check():
    """Moving the check must not have moved this. Writing it before the check
    would mean writing into a package that has not been verified."""
    source = (APP / "run_app.py").read_text(encoding="utf-8")
    assert source.index("packaging.verify(ROOT)") < source.index("startup.write_runtime(")


def test_no_second_tab_is_opened_when_the_screen_is_up():
    source = (APP / "run_app.py").read_text(encoding="utf-8")
    body = source[source.index("def when_up():"):source.index("def tidy_cache():")]
    assert "if not showing:" in body, "it opens the app on top of the loading screen"


def test_the_splash_ships_inside_the_package():
    """It runs before uvicorn is imported, so it has to be there in a package
    whose wheels are the thing that went missing."""
    source = (APP / "server" / "splash.py").read_text(encoding="utf-8")
    for third_party in ("import fastapi", "import uvicorn", "import anthropic", "import PIL"):
        assert third_party not in source, third_party

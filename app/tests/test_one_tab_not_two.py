"""Double-clicking the icon opens one tab, not two.

North star line 4: he is never shown an old screen. Two tabs is that fault
wearing different clothes, because one of them is a loading page that has
already been left behind.

The history matters, because the obvious fix is the one that was already tried
and reverted. The loading page used to be the only thing that moved him over,
and the launcher only opened the app when no page had been drawn. On Mark's
Windows machine on 2026-09-14 the page could not reach the app at all, so
nothing moved him over and the app ran with nobody looking at it. The launcher
was made to open the app every time, which costs a spare tab when the page did
work. Spenser has since watched the page work on his own machine, so both
outcomes happen and nobody knows why.

So the page now says when it has arrived, and the launcher opens its own tab
only when nothing has said so. Whatever the browser blocks, the app is still
in front of somebody: being blocked is exactly when the page cannot tell
anybody anything, and that is the case the launcher's own tab is for.
"""
import ast
import sys
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))
sys.path.insert(0, str(APP))

import splash  # noqa: E402
import startup  # noqa: E402
from main import create_app  # noqa: E402

RUN_APP = (APP / "run_app.py").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def nothing_has_arrived_yet():
    """The flag lasts one process, and the test process is one process."""
    startup.forget_the_loading_page()
    yield
    startup.forget_the_loading_page()


# --- the page says it got there ---------------------------------------------

def test_the_page_asks_the_app_on_the_path_that_records_it():
    """It already asks the app whether it is up. Now the asking is the news."""
    page = splash.page(51234, "0.6.8")
    assert startup.LOADING_PAGE_PATH in page
    assert "http://127.0.0.1:51234%s" % startup.LOADING_PAGE_PATH in page


def test_the_page_still_moves_itself_over_to_the_app_itself():
    """It announces itself on one path and then goes to the app, not to the
    path it announced itself on."""
    page = splash.page(51234, "0.6.8")
    assert 'window.location.replace("http://127.0.0.1:51234/")' in page \
        or 'location.replace(app)' in page
    assert "window.open" not in page


# --- what the app knows ------------------------------------------------------

def test_the_app_assumes_nothing_arrived():
    """Silence is the blocked case, and the blocked case must open a tab."""
    assert startup.wait_for_the_loading_page(0.05) is False


def test_the_route_is_what_tells_the_app():
    client = TestClient(create_app())
    assert startup.wait_for_the_loading_page(0.01) is False
    assert client.get(startup.LOADING_PAGE_PATH).status_code == 200
    assert startup.wait_for_the_loading_page(0.01) is True


def test_it_stops_waiting_the_moment_the_page_arrives():
    """He does not wait out the whole patience when the page is not blocked."""
    threading.Timer(0.05, startup.the_loading_page_arrived).start()
    began = time.monotonic()
    assert startup.wait_for_the_loading_page(5.0) is True
    assert time.monotonic() - began < 2.0


def test_the_wait_is_short_enough_to_sit_through():
    """What he waits in the blocked case, with the app already up behind it."""
    import run_app
    assert 0 < run_app.HANDOVER_SECONDS <= 8


# --- the launcher ------------------------------------------------------------

def _when_up() -> ast.FunctionDef:
    tree = ast.parse(RUN_APP)
    return [n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "when_up"][0]


def _the_handover_branch() -> ast.If:
    for node in ast.walk(_when_up()):
        if isinstance(node, ast.If) and "wait_for_the_loading_page" in ast.dump(node.test):
            return node
    raise AssertionError("nothing in when_up waits for the loading page")


def test_the_launcher_waits_for_the_page_before_opening_anything():
    body = RUN_APP[RUN_APP.index("def when_up():"):RUN_APP.index("def tidy_cache():")]
    assert body.index("wait_for_the_loading_page") < body.index("webbrowser.open(")


def test_the_launcher_opens_the_app_when_nothing_arrived():
    """The whole reason this is not simply the old skip put back."""
    branch = _the_handover_branch()
    taken = ast.dump(ast.Module(body=branch.body, type_ignores=[]))
    not_taken = ast.dump(ast.Module(body=branch.orelse, type_ignores=[]))
    assert "webbrowser" in taken, "nothing opens the app when the page is blocked"
    assert "webbrowser" not in not_taken, "it opens a second tab after a handover"


def test_a_page_that_was_never_drawn_is_not_waited_for():
    """`splash.show` returning False means there is nobody to hear from, so
    there is nothing to wait for and the app opens straight away."""
    assert "showing = splash.show(" in RUN_APP
    branch = ast.dump(_the_handover_branch().test)
    assert "showing" in branch

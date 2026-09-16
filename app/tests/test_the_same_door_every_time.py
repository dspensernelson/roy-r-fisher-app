"""The app answers on the same number every time, so a tab can find it again.

**What Spenser approved on 2026-09-16, in his words and mine.** When Colleen
presses Update, her tab should keep quietly asking the same address until the
new version answers, and then reload itself into it. One tab. No message,
nothing for her to close. Today the number is different on every start, so the
tab she pressed Update in can never find the new app and sits there dead.

**Why a fixed number is safe here.** One machine, one user, one app. The
launcher already stops any copy that is running before it starts, so the app
is never competing with itself for the number.

**Why the fallback still exists.** Something else on the machine can be
holding it. In that case the app takes any free number and behaves exactly as
it does today: the old tab cannot find it and the new app opens its own. That
is the floor, and the floor is where we already live.

Nothing here binds a real port except where it says so.
"""
import socket
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "app" / "server"))

import startup   # noqa: E402


def test_the_same_number_comes_back_every_time():
    assert startup.the_usual_port() == startup.the_usual_port()
    assert startup.the_usual_port() == startup.USUAL_PORT


def test_the_number_is_one_the_operating_system_will_not_hand_out():
    """Windows hands out ephemeral ports from 49152 upward. Sitting below that
    is what stops something else being given ours while we are not running."""
    assert 1024 < startup.USUAL_PORT < 49152


def test_it_takes_the_usual_number_when_nothing_holds_it():
    assert startup.pick_a_port() == startup.USUAL_PORT


def test_it_takes_any_free_number_when_something_holds_the_usual_one():
    """The floor. She is back to today's behaviour for that one start, which
    is a stale tab, rather than an app that will not open at all."""
    held = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    held.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        held.bind((startup.BIND_HOST, startup.USUAL_PORT))
        held.listen(1)
        picked = startup.pick_a_port()
    finally:
        held.close()
    assert picked != startup.USUAL_PORT
    assert picked > 0


def test_a_port_it_picks_can_actually_be_bound():
    picked = startup.pick_a_port()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((startup.BIND_HOST, picked))


def test_three_minutes_before_it_says_anything():
    """Spenser, 2026-09-16: "make it wait 3 minutes". An update unpacks and
    copies sixty megabytes, and a slow machine genuinely takes that long. A
    sentence that arrives while the thing is still working is a lie."""
    assert startup.PATIENCE_SECONDS == 180


# ---------------------------------------------- the handover from an update ---

def test_the_launcher_is_told_when_a_tab_is_coming_back(monkeypatch):
    """The new app must not open a tab of its own when the old one is on its
    way back to the same number, or the fix produces two tabs instead of one.

    It is told through the environment rather than asked to work it out,
    because the only thing that knows an update is happening is the thing that
    started it."""
    monkeypatch.delenv(startup.HANDING_OVER, raising=False)
    assert startup.a_tab_is_coming_back() is False
    monkeypatch.setenv(startup.HANDING_OVER, "1")
    assert startup.a_tab_is_coming_back() is True


def test_anything_but_one_means_no(monkeypatch):
    """A stale variable left in a shell is not an update in progress."""
    for value in ("", "0", "yes", "true"):
        monkeypatch.setenv(startup.HANDING_OVER, value)
        assert startup.a_tab_is_coming_back() is False


def test_it_waits_longer_for_a_returning_tab_than_for_a_loading_page():
    """A loading page is already open and answering in milliseconds. A tab
    coming back from an update is waiting on a whole app to start, so the
    window before giving up and opening one has to be wider."""
    assert startup.HANDOVER_FROM_UPDATE_SECONDS > 5.0


def test_the_update_tells_the_new_version_a_tab_is_coming(monkeypatch):
    sys.path.insert(0, str(REPO / "app"))
    import update_apply                                    # noqa: E402

    seen = {}

    def spy(command, **options):
        seen.update(options)
        seen["command"] = command

    monkeypatch.delenv(startup.HANDING_OVER, raising=False)
    assert update_apply.start_new_version(REPO / "Start Roy R. Fisher.bat", spawn=spy)
    assert seen["env"][startup.HANDING_OVER] == "1"
    # The rest of the environment has to survive: PATH among it, or `cmd.exe`
    # is not found and nothing starts at all.
    assert len(seen["env"]) > 1

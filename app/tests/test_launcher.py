"""Picking a port, finding our own copy, and refusing somebody else's.

Everything here runs against a real loopback socket and real folders in
tmp_path. The one thing stood in for is the answer on a port, which is exactly
the "are we on Windows" style of stand-in the working rules allow: it lets a
version that is not ours, and a port that answers nothing, both be tested
without a second app installed.
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import startup  # noqa: E402


class Answering:
    """A real HTTP server on a real port that answers /api/version.

    A real socket rather than a patched function, because what is being proved
    is that the probe talks to something on a port and believes only the right
    answer.
    """

    def __init__(self, body, path="/api/version"):
        self.body = body
        self.path = path
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != parent.path:
                    self.send_response(404)
                    self.end_headers()
                    return
                payload = json.dumps(parent.body).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]

    def __enter__(self):
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def code_only(path: Path) -> str:
    """The file's executable code, with comments and string literals removed.

    Written because two earlier versions of these tests matched words in the
    module's own docstring, which explains the very things they were checking
    were absent. Prose about 8000 is not a use of 8000.
    """
    import io
    import tokenize

    kept = []
    with open(path, "rb") as handle:
        for token in tokenize.tokenize(handle.readline):
            if token.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            kept.append(token.string)
    return " ".join(kept)


def folder(root: Path, name: str, port=None, version=None) -> Path:
    """An installed version folder, optionally one that has run before."""
    place = root / name
    place.mkdir(parents=True, exist_ok=True)
    if port is not None:
        startup.write_runtime(place, port, version or "0.0.0")
    return place


# --- the port ---------------------------------------------------------------

def test_it_asks_the_operating_system_for_a_port():
    port = startup.free_port()
    assert 1024 < port < 65536
    assert port != 8000              # never the old hardcoded one, by luck or not


def test_two_asks_do_not_collide():
    assert startup.free_port() != 0
    assert len({startup.free_port() for _ in range(5)}) >= 1


def test_it_binds_loopback_only():
    """Never 0.0.0.0. A loopback-only bind usually avoids the Windows firewall
    prompt, and an unsigned launcher opening a socket is already conspicuous."""
    assert startup.BIND_HOST == "127.0.0.1"
    assert startup.HOST == "127.0.0.1"
    assert "0.0.0.0" not in code_only(Path(startup.__file__))


def test_there_is_no_walk_up_from_8000():
    """The rejected alternative. It starts a second copy instead of finding
    the first, and it never terminates if something answers on every port."""
    code = code_only(Path(startup.__file__))
    assert "8000" not in code
    # the only loop in the module is the bounded wait, which has a deadline
    import ast
    tree = ast.parse(Path(startup.__file__).read_text(encoding="utf-8"))
    looping = [n for n in ast.walk(tree) if isinstance(n, (ast.While, ast.For))]
    enclosing = set()
    for func in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        if any(loop in ast.walk(func) for loop in looping):
            enclosing.add(func.name)
    assert enclosing <= {"wait_until_answering", "wait_until_it_stops",
                         "running_sibling", "copies_running",
                         "stop_the_running_copies"}, enclosing


# --- runtime.json -----------------------------------------------------------

def test_it_records_and_rereads_the_bound_port(tmp_path):
    startup.write_runtime(tmp_path, 51234, "0.1.0")
    recorded = startup.read_runtime(tmp_path)
    assert recorded["port"] == 51234
    assert recorded["version"] == "0.1.0"


def test_a_folder_that_never_ran_has_nothing_recorded(tmp_path):
    assert startup.read_runtime(tmp_path) == {}


def test_a_damaged_runtime_file_says_nothing_rather_than_raising(tmp_path):
    startup.runtime_file(tmp_path).write_text("{not json", encoding="utf-8")
    assert startup.read_runtime(tmp_path) == {}


def test_writing_it_leaves_no_leftover(tmp_path):
    startup.write_runtime(tmp_path, 51234, "0.1.0")
    assert not list(tmp_path.glob("*.writing"))


# --- the probe --------------------------------------------------------------

def test_it_reads_the_version_that_answers():
    with Answering({"version": "0.2.0"}) as server:
        assert startup.ask_version(server.port) == "0.2.0"


def test_nothing_listening_is_not_an_answer():
    port = startup.free_port()
    assert startup.ask_version(port, timeout=0.4) == ""


def test_something_that_is_not_our_app_is_not_an_answer():
    with Answering({"hello": "I am something else"}) as server:
        assert startup.ask_version(server.port) == ""


def test_something_answering_a_different_path_is_not_an_answer():
    with Answering({"version": "0.2.0"}, path="/something-else") as server:
        assert startup.ask_version(server.port) == ""


# --- this same version already running --------------------------------------

def test_it_finds_our_own_copy_and_returns_its_port(tmp_path):
    with Answering({"version": "0.1.0"}) as server:
        here = folder(tmp_path, "Roy R. Fisher v0.1.0", server.port, "0.1.0")
        assert startup.already_running_here(here, "0.1.0") == server.port


def test_a_different_version_on_our_recorded_port_is_never_accepted(tmp_path):
    """The defect this closes: a version-blind probe served v2 when Mark
    double-clicked v1 to roll back, and it looked like it had worked."""
    with Answering({"version": "9.9.9"}) as server:
        here = folder(tmp_path, "Roy R. Fisher v0.1.0", server.port, "0.1.0")
        assert startup.already_running_here(here, "0.1.0") == 0


def test_a_stale_recorded_port_that_answers_nothing_is_not_running(tmp_path):
    here = folder(tmp_path, "Roy R. Fisher v0.1.0", startup.free_port(), "0.1.0")
    assert startup.already_running_here(here, "0.1.0") == 0


# --- another version running beside us --------------------------------------
# It is stopped rather than refused, since 0.7.1. What is unchanged is that two
# copies never write the home folder at the same time: one of them goes first.

def test_a_live_sibling_version_is_found(tmp_path):
    with Answering({"version": "0.2.0"}) as server:
        beside = folder(tmp_path, "Roy R. Fisher v0.2.0", server.port, "0.2.0")
        here = folder(tmp_path, "Roy R. Fisher v0.1.0")
        assert startup.running_sibling(here) == (beside, "0.2.0")


def test_a_sibling_that_has_run_before_but_is_closed_is_not_alive(tmp_path):
    """The ordinary case after a rollback: the other folder is still there and
    still remembers a port, and nothing is listening on it."""
    folder(tmp_path, "Roy R. Fisher v0.2.0", startup.free_port(), "0.2.0")
    here = folder(tmp_path, "Roy R. Fisher v0.1.0")
    assert startup.running_sibling(here) is None


def test_a_sibling_that_has_never_run_is_not_alive(tmp_path):
    folder(tmp_path, "Roy R. Fisher v0.2.0")
    here = folder(tmp_path, "Roy R. Fisher v0.1.0")
    assert startup.running_sibling(here) is None


def test_our_own_folder_is_never_its_own_sibling(tmp_path):
    with Answering({"version": "0.1.0"}) as server:
        here = folder(tmp_path, "Roy R. Fisher v0.1.0", server.port, "0.1.0")
        assert startup.sibling_folders(here) == []
        assert startup.running_sibling(here) is None


# --- stopping the copy that is already running ------------------------------
# Until 0.7.1 the launcher refused here and told Mark to close a window. There
# is no window: the app has run with no console since 0.6.5, and the tab it
# opened may have been closed hours ago. So it asked him to do something
# impossible and left him nowhere to go but Task Manager.


class Copy:
    """A running copy of the app, on a real port, that can be asked to stop.

    Real sockets for the same reason as `Answering` above: what is being proved
    is that one copy of the app talks to another over a port, in the way the
    Settings screen's `Close the app` button already does.

    `stubborn` answers the request and then keeps answering anyway, which is
    the case the launcher has to be able to say something useful about.
    `deaf` is a copy too old to have the route at all.
    """

    def __init__(self, version="0.1.0", stubborn=False, deaf=False):
        self.version = version
        self.stubborn = stubborn
        self.deaf = deaf
        self.alive = True
        self.asked = 0
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/api/version" or not parent.alive:
                    self.send_response(404)
                    self.end_headers()
                    return
                payload = json.dumps({"version": parent.version}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_POST(self):
                if self.path != startup.CLOSE_PATH or parent.deaf:
                    self.send_response(404)
                    self.end_headers()
                    return
                parent.asked += 1
                payload = b'{"closing": true}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                if not parent.stubborn:
                    parent.alive = False

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]

    def __enter__(self):
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def test_it_asks_over_the_route_the_close_button_already_uses():
    """One way to stop the app, not two. The Settings screen posts to this
    same path, and the path is owned here so the two cannot drift apart."""
    assert startup.CLOSE_PATH == "/api/close"
    with Copy("0.1.0") as copy:
        assert startup.ask_it_to_stop(copy.port) is True
        assert copy.asked == 1


def test_a_copy_without_that_route_is_never_reported_as_stopping():
    with Copy("0.1.0", deaf=True) as copy:
        assert startup.ask_it_to_stop(copy.port) is False


def test_nothing_listening_is_not_a_yes():
    assert startup.ask_it_to_stop(startup.free_port(), timeout=0.4) is False


def test_the_wait_ends_when_the_copy_stops_answering():
    """Polled, never slept through. A fixed sleep is a guess that is too long
    on a fast machine and too short on Mark's."""
    with Copy("0.1.0") as copy:
        startup.ask_it_to_stop(copy.port)
        assert startup.wait_until_it_stops(copy.port, "0.1.0", timeout=5.0) is True


def test_the_wait_gives_up_rather_than_waiting_forever():
    with Copy("0.1.0", stubborn=True) as copy:
        startup.ask_it_to_stop(copy.port)
        assert startup.wait_until_it_stops(
            copy.port, "0.1.0", timeout=0.6,
            sleep=[].append, now=_ticking()) is False


def test_the_wait_is_long_enough_for_a_copy_finishing_a_write():
    """The copy being stopped waits for its own writes to finish before it
    goes. Giving up sooner than it takes would call a working close a failure.
    Its numbers are not read from here: it is another program, possibly an
    older build of it, so its constants are not ours to reach into."""
    assert startup.STOP_TIMEOUT >= 35.0


# --- finding every copy that is running ------------------------------------

def test_a_copy_running_in_this_very_folder_is_found(tmp_path):
    """The second branch of the same fault. Until 0.7.1 this case opened a
    browser at whatever was running, and four builds in one day all called
    themselves 0.7.0, so a freshly unpacked build handed him a stale one."""
    with Copy("0.1.0") as copy:
        here = folder(tmp_path, "Roy R. Fisher v0.1.0", copy.port, "0.1.0")
        found = startup.copies_running(here)
        assert [(f.name, v, p) for f, v, p in found] == [
            ("Roy R. Fisher v0.1.0", "0.1.0", copy.port)]


def test_a_copy_running_beside_this_one_is_found(tmp_path):
    with Copy("0.2.0") as copy:
        folder(tmp_path, "Roy R. Fisher v0.2.0", copy.port, "0.2.0")
        here = folder(tmp_path, "Roy R. Fisher v0.1.0")
        found = startup.copies_running(here)
        assert [(f.name, v, p) for f, v, p in found] == [
            ("Roy R. Fisher v0.2.0", "0.2.0", copy.port)]


def test_a_folder_that_has_run_before_and_is_closed_is_not_a_running_copy(tmp_path):
    folder(tmp_path, "Roy R. Fisher v0.2.0", startup.free_port(), "0.2.0")
    here = folder(tmp_path, "Roy R. Fisher v0.1.0")
    assert startup.copies_running(here) == []


# --- taking over ------------------------------------------------------------

def test_the_copy_that_was_running_is_stopped_and_this_one_carries_on(tmp_path):
    with Copy("0.2.0") as copy:
        folder(tmp_path, "Roy R. Fisher v0.2.0", copy.port, "0.2.0")
        here = folder(tmp_path, "Roy R. Fisher v0.1.0")

        startup.stop_the_running_copies(startup.copies_running(here))

        assert copy.asked == 1
        assert copy.alive is False
        assert startup.copies_running(here) == []


def test_nothing_running_means_nothing_to_stop(tmp_path):
    here = folder(tmp_path, "Roy R. Fisher v0.1.0")
    startup.stop_the_running_copies(startup.copies_running(here))   # no raise


def test_it_says_what_it_is_doing_while_it_does_it(tmp_path):
    """The first thing he sees. Silence reads as a failed click."""
    said = []
    with Copy("0.2.0") as copy:
        folder(tmp_path, "Roy R. Fisher v0.2.0", copy.port, "0.2.0")
        here = folder(tmp_path, "Roy R. Fisher v0.1.0")
        startup.stop_the_running_copies(startup.copies_running(here), say=said.append)

    spoken = " ".join(said).lower()
    assert "0.2.0" in spoken
    assert "clos" in spoken


def test_a_copy_that_will_not_stop_finally_says_so(tmp_path):
    with Copy("0.2.0", stubborn=True) as copy:
        folder(tmp_path, "Roy R. Fisher v0.2.0", copy.port, "0.2.0")
        here = folder(tmp_path, "Roy R. Fisher v0.1.0")

        with pytest.raises(startup.StartupRefused) as raised:
            startup.stop_the_running_copies(
                startup.copies_running(here), timeout=0.6,
                sleep=[].append, now=_ticking())

    message = raised.value.message
    assert "0.2.0" in message
    assert "Roy R. Fisher v0.2.0" in message
    assert str(copy.port) in message
    assert "Traceback" not in message


def test_it_never_asks_him_to_close_a_window_that_is_not_there(tmp_path):
    """The whole defect. There has been no window since 0.6.5."""
    message = startup.would_not_stop(tmp_path, "0.2.0", 51234)
    assert "window" not in message.lower()
    assert "Close that window first" not in message


def test_it_says_what_it_already_tried_before_it_asks_him_for_anything(tmp_path):
    message = startup.would_not_stop(tmp_path, "0.2.0", 51234)
    tried = message.lower().index("asked it to close")
    assert tried < message.lower().index("restart")


def test_there_is_always_something_he_can_do(tmp_path):
    message = startup.would_not_stop(tmp_path, "0.2.0", 51234).lower()
    assert "restart" in message
    assert "double-click" in message


def test_task_manager_is_the_last_thing_said_and_never_the_first(tmp_path):
    """Acceptable as a last line to an appraiser. Not acceptable as the only
    thing on offer, which is what 0.7.0 left him with."""
    message = startup.would_not_stop(tmp_path, "0.2.0", 51234)
    said = message.lower()
    assert "task manager" in said
    assert said.index("restart") < said.index("task manager")
    last = [line for line in message.splitlines() if line.strip()][-1]
    assert "task" in last.lower() or "end task" in last.lower()


# --- the order the launcher does it in --------------------------------------

def test_the_launcher_stops_the_old_copy_rather_than_refusing():
    source = (Path(__file__).resolve().parents[1] / "run_app.py").read_text(encoding="utf-8")
    assert "stop_the_running_copies" in source
    assert "refuse_if_another_version_runs" not in source


def test_the_launcher_never_just_opens_whatever_is_already_running():
    """Two builds can wear the same number, and /api/version cannot tell them
    apart, so 'it is already running' is not a thing the app can know."""
    source = (Path(__file__).resolve().parents[1] / "run_app.py").read_text(encoding="utf-8")
    assert "is already running. Opening it." not in source


def test_the_screen_says_so_before_the_waiting_starts():
    source = (Path(__file__).resolve().parents[1] / "run_app.py").read_text(encoding="utf-8")
    assert source.index("splash.show(") < source.index("stop_the_running_copies")


def test_stopping_the_old_copy_happens_before_this_one_binds_anything():
    source = (Path(__file__).resolve().parents[1] / "run_app.py").read_text(encoding="utf-8")
    assert source.index("stop_the_running_copies") < source.index("import uvicorn")
    assert source.index("stop_the_running_copies") < source.index("write_runtime")


# --- waiting, and giving up ------------------------------------------------

def test_it_waits_for_our_own_version_before_saying_yes():
    with Answering({"version": "0.1.0"}) as server:
        assert startup.wait_until_answering(server.port, "0.1.0", timeout=3.0) is True


def test_it_never_reports_success_for_a_different_version():
    with Answering({"version": "9.9.9"}) as server:
        slept = []
        assert startup.wait_until_answering(
            server.port, "0.1.0", timeout=0.6,
            sleep=slept.append, now=_ticking()) is False


def test_it_gives_up_rather_than_waiting_forever():
    port = startup.free_port()
    slept = []
    assert startup.wait_until_answering(
        port, "0.1.0", timeout=0.6, sleep=slept.append, now=_ticking()) is False


def _ticking():
    """A clock that advances a quarter second each time it is read, so the
    timeout tests finish immediately instead of really waiting."""
    state = {"t": 0.0}

    def now():
        state["t"] += 0.25
        return state["t"]
    return now


def test_the_failure_report_is_plain_and_names_what_was_tried(tmp_path):
    report = startup.failure_report(tmp_path, 51234, "0.1.0")
    assert "0.1.0" in report
    assert "51234" in report
    assert str(tmp_path) in report
    assert "Traceback" not in report
    assert "Exception" not in report
    assert "send Spenser" in report


# --- the order the launcher does things in ----------------------------------

def test_the_launcher_checks_the_package_before_importing_uvicorn():
    """A damaged package must be able to say so. uvicorn is imported last on
    purpose, because a missing wheel is exactly what goes wrong."""
    source = (Path(__file__).resolve().parents[1] / "run_app.py").read_text(encoding="utf-8")
    assert source.index("packaging.verify") < source.index("import uvicorn")
    assert source.index("copies_running") < source.index("import uvicorn")
    # and the verify happens before runtime.json is written or touched
    assert source.index("packaging.verify") < source.index("write_runtime")


def test_the_launcher_opens_the_browser_only_after_a_real_answer():
    source = (Path(__file__).resolve().parents[1] / "run_app.py").read_text(encoding="utf-8")
    assert "threading.Timer(1.0" not in source          # the old guess
    assert source.index("wait_until_answering") < source.index("webbrowser.open(\"http://%s:%d\" % (startup.HOST, port))")


def test_the_last_good_record_waits_twenty_seconds():
    """Twenty seconds after a real answer, not before it, and from inside the
    process that is serving so the timer firing is itself the evidence that
    the process was still alive."""
    import ast

    path = Path(__file__).resolve().parents[1] / "run_app.py"
    source = path.read_text(encoding="utf-8")
    assert "GOOD_AFTER_SECONDS = 20.0" in source

    tree = ast.parse(source)
    when_up = [n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "when_up"][0]
    body = ast.dump(when_up)
    # the record is scheduled inside the branch that waited for a real answer
    guard = [n for n in ast.walk(when_up) if isinstance(n, ast.If)][0]
    assert "wait_until_answering" in ast.dump(guard.test)
    assert "_record_last_good" in ast.dump(ast.Module(body=guard.body, type_ignores=[]))
    assert "_record_last_good" not in ast.dump(
        ast.Module(body=guard.orelse, type_ignores=[]))
    assert "GOOD_AFTER_SECONDS" in body


def test_both_launchers_are_thin_shims():
    """The port logic is written once, in Python, not once in batch and once
    in bash."""
    repo = Path(__file__).resolve().parents[2]
    bat = (repo / "Start Roy R. Fisher.bat").read_text(encoding="utf-8")
    command = (repo / "Start Roy R. Fisher.command").read_text(encoding="utf-8")

    for shim in (bat, command):
        assert "8000" not in shim
        assert "curl" not in shim
    assert "run_app.py" in bat and "run_app.py" in command

    # No console, changed 2026-09-03. `pythonw.exe` is the same Python beside
    # `python.exe`, built to run without one. The black window was the first
    # thing anybody saw every time they started the app.
    assert "pythonw.exe" in bat
    # And therefore no pause: there is no window to hold open, and nothing is
    # printed to read. A failure arrives as a message box instead, through
    # `app/server/tell.py`, which is the piece that had to exist before the
    # window could go.
    assert "pause" not in bat.lower()


# --- one icon, and it is the firm's ---------------------------------------
# Spenser ended up with two icons on his Desktop on 2026-09-03, one of them
# dead, and the live one wearing Python's logo. Both were consequences of
# pointing the shortcut straight at pythonw.exe to get rid of the black window.

def test_the_icon_file_ships_with_the_app():
    """Windows reads it off disk when the shortcut is made, so it has to be
    inside the package rather than beside it in the repository."""
    icon = Path(__file__).resolve().parents[2] / "app" / "data" / "rrf.ico"
    assert icon.is_file()
    assert icon.stat().st_size > 1000

    from PIL import Image
    with Image.open(icon) as im:
        sizes = sorted(im.info.get("sizes", []))
    # Windows picks a size per place it draws it. Without a small one it
    # shrinks the big one and the bars turn to mush in the taskbar.
    assert (16, 16) in sizes and (256, 256) in sizes


def test_the_shortcut_names_that_icon():
    source = (Path(__file__).resolve().parents[2] / "app" / "install_windows.py").read_text()
    assert "IconLocation" in source
    assert "rrf.ico" in source


def test_installing_clears_the_other_icon_away():
    """The fallback .bat already removes a stale .lnk when it takes over. This
    is the other half. Without it a Desktop collects one of each, and the .bat
    points at a single version folder that the installer will later prune."""
    source = (Path(__file__).resolve().parents[2] / "app" / "install_windows.py").read_text()
    assert "_remove_stale(desktop / FALLBACK_NAME)" in source

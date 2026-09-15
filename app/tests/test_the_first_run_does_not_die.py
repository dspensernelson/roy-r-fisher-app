"""B15. Every new version died the first time it ran, and said nothing.

Proven on Spenser's Windows machine on 2026-09-15. A version that has never
run before has no compiled cache, so the three background jobs the launcher
started had to compile hundreds of files. uvicorn was imported on the very next
line, its import chain reached `dataclasses` while a background job still had
`typing` half built, and it died:

    AttributeError: partially initialized module 'typing' has no attribute
    'ClassVar' (most likely due to a circular import)

Two things are proved here, and neither can be proved by starting the app.

**The order.** Every machine this suite runs on is warm, so a test that starts
the app would pass whichever order the file is in. So the order itself is the
thing tested: on the source, the way `test_the_click_shows_something.py`
already tests the order of the loading screen, and again while `_start` really
runs, with uvicorn and the threads stood in for.

**The message.** The crash hid for a week because the launcher spoke for two
named failures and let everything else die with its output going nowhere, since
the shortcut runs `pythonw.exe`, which has no console. Anything unexpected now
reaches the log and a message box, and says what to do.
"""
import ast
import importlib.abc
import importlib.util
import sys
import types
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))
sys.path.insert(0, str(APP))

import applog  # noqa: E402
import run_app  # noqa: E402
import tell  # noqa: E402

SOURCE = (APP / "run_app.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

THREADS = ("Thread", "Timer")


# --- reading the source ------------------------------------------------------

def _uvicorn_import():
    for node in ast.walk(TREE):
        if isinstance(node, ast.Import) and any(a.name == "uvicorn" for a in node.names):
            return node
    raise AssertionError("nothing in run_app.py imports uvicorn")


def _holding_function(statement):
    """The function whose own body holds this statement, not a nested one."""
    for node in ast.walk(TREE):
        if isinstance(node, ast.FunctionDef):
            if any(held is statement for held in node.body):
                return node
    raise AssertionError("the uvicorn import is not inside a function")


def _runs_now(function):
    """The statements that run when the function is called.

    A `def` inside it is not one of them: defining `when_up` does not start
    anything, and the timer inside it fires from a thread that this file no
    longer starts until uvicorn is loaded.
    """
    return [s for s in function.body
            if not isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _thread_starts(statement):
    """Every `threading.Thread(...).start()` shaped call inside a statement."""
    found = []
    for node in ast.walk(statement):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr != "start":
            continue
        made = node.func.value
        if isinstance(made, ast.Call):
            named = made.func
            if isinstance(named, ast.Attribute) and named.attr in THREADS:
                found.append(node)
            elif isinstance(named, ast.Name) and named.id in THREADS:
                found.append(node)
    return found


def test_no_background_job_is_started_before_uvicorn_is_imported():
    """The fault itself. On a cold machine the threads compile hundreds of
    files, and the uvicorn import walks into one of them half built."""
    imported = _uvicorn_import()
    starting = _holding_function(imported)
    for statement in _runs_now(starting):
        for start in _thread_starts(statement):
            assert start.lineno > imported.lineno, (
                "a background job is started on line %d, before uvicorn is "
                "imported on line %d" % (start.lineno, imported.lineno))


def test_all_three_background_jobs_still_start():
    """Moving them must not have lost one."""
    imported = _uvicorn_import()
    starting = _holding_function(imported)
    started = [s for statement in _runs_now(starting)
               for s in _thread_starts(statement)]
    assert len(started) == 3, "there should be three, there are %d" % len(started)
    targets = set()
    for start in started:
        for word in start.func.value.keywords:
            if word.arg == "target" and isinstance(word.value, ast.Name):
                targets.add(word.value.id)
    assert targets == {"tidy_cache", "look_for_an_update", "when_up"}


# --- watching it actually happen ---------------------------------------------

class _Stub(importlib.abc.Loader):
    """A stand-in uvicorn that records the moment it is imported."""

    def __init__(self, events):
        self.events = events

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        self.events.append("uvicorn imported")
        module.run = lambda *a, **k: self.events.append("uvicorn.run")


class _Watcher(importlib.abc.MetaPathFinder):
    def __init__(self, events):
        self.events = events

    def find_spec(self, fullname, path=None, target=None):
        if fullname != "uvicorn":
            return None
        return importlib.util.spec_from_loader(fullname, _Stub(self.events))


def test_nothing_is_running_in_the_background_while_uvicorn_loads(monkeypatch):
    """The same claim as above, proved while the launcher really runs.

    Reading the source cannot see a thread started by something the launcher
    calls. This can: it records every start and the import, in the order they
    happen.
    """
    events = []

    class Recorder:
        def __init__(self, target=None, daemon=None, **_rest):
            self.target = target

        def start(self):
            events.append("started %s" % getattr(self.target, "__name__", self.target))

    monkeypatch.setattr(run_app, "threading",
                        types.SimpleNamespace(Thread=Recorder, Timer=Recorder))
    monkeypatch.setattr(run_app.startup, "copies_running", lambda home: [])
    monkeypatch.setattr(run_app.startup, "free_port", lambda: 51234)
    monkeypatch.setattr(run_app.startup, "stop_the_running_copies",
                        lambda running, say=None: None)
    monkeypatch.setattr(run_app.startup, "write_runtime", lambda *a, **k: None)
    monkeypatch.setattr(run_app.startup, "clear_runtime", lambda *a, **k: None)
    monkeypatch.setattr(run_app.packaging, "is_checkout", lambda root: True)
    monkeypatch.setattr(run_app.splash, "show", lambda *a, **k: False)
    monkeypatch.setattr(run_app.tell, "say", lambda message: None)

    monkeypatch.delitem(sys.modules, "uvicorn", raising=False)
    watcher = _Watcher(events)
    monkeypatch.setattr(sys, "meta_path", [watcher] + sys.meta_path)

    assert run_app._start() == 0
    assert events[0] == "uvicorn imported", \
        "something ran in the background before uvicorn was loaded: %r" % events
    assert events[-1] == "uvicorn.run"
    assert len([e for e in events if e.startswith("started ")]) == 3


# --- saying what killed it ---------------------------------------------------

class Caught:
    """Everything the launcher said, and where it tried to say it."""

    def __init__(self, monkeypatch, tmp_path):
        self.shown = []
        monkeypatch.setenv("RRF_LOG_FILE", str(tmp_path / ".rrf-app.log"))
        monkeypatch.setattr(run_app.tell, "problem", self.shown.append)
        self.log = tmp_path / ".rrf-app.log"

    def written(self):
        return self.log.read_text(encoding="utf-8") if self.log.is_file() else ""


def _dies_with(monkeypatch, exc):
    def boom():
        raise exc
    monkeypatch.setattr(run_app, "_start", boom)


def test_a_failure_nobody_expected_is_still_said_out_loud(monkeypatch, tmp_path):
    """The week this cost. `pythonw.exe` has no console, so an unhandled
    exception went nowhere at all."""
    caught = Caught(monkeypatch, tmp_path)
    _dies_with(monkeypatch, AttributeError(
        "partially initialized module 'typing' has no attribute 'ClassVar'"))
    run_app.main()
    assert len(caught.shown) == 1
    assert "ClassVar" in caught.shown[0]


def test_a_failure_nobody_expected_reaches_the_log(monkeypatch, tmp_path):
    """A message box is read once and clicked away. The log is what Spenser
    can be sent afterwards."""
    caught = Caught(monkeypatch, tmp_path)
    _dies_with(monkeypatch, AttributeError("half built"))
    run_app.main()
    written = caught.written()
    assert "half built" in written
    assert "run_app.py" in written, "the log has no traceback in it"


def test_it_says_what_to_do_and_not_only_what_broke(monkeypatch, tmp_path):
    caught = Caught(monkeypatch, tmp_path)
    _dies_with(monkeypatch, RuntimeError("something nobody has seen before"))
    run_app.main()
    said = caught.shown[0]
    assert "again" in said.lower(), "it does not tell him to try again"
    assert applog.LOG_NAME in said, "it does not say which file to send"


def test_it_does_not_report_success_when_it_died(monkeypatch, tmp_path):
    Caught(monkeypatch, tmp_path)
    _dies_with(monkeypatch, RuntimeError("dead"))
    assert run_app.main() != 0


def test_stopping_it_yourself_is_not_a_failure(monkeypatch, tmp_path):
    """Control-C on the Mac is how the app is stopped on purpose. It is not
    something to raise a box about."""
    caught = Caught(monkeypatch, tmp_path)
    _dies_with(monkeypatch, KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        run_app.main()
    assert caught.shown == []


def test_the_failures_it_already_spoke_for_are_unchanged(monkeypatch, tmp_path):
    """A damaged package still returns 2 and still says its own sentence.
    Wrapping everything must not have turned a good message into a traceback."""
    caught = Caught(monkeypatch, tmp_path)
    monkeypatch.setattr(run_app, "_start", lambda: 2)
    assert run_app.main() == 2
    assert caught.shown == []

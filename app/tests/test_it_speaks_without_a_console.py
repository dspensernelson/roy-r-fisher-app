"""A failure is still visible once the black window is gone.

Spenser, 2026-09-03: *"I just want the app to open like an app."* The console
window sat in front of the app the whole time it ran, and it is the first thing
anybody saw.

`pythonw.exe` ships inside the package and runs without one. The reason it was
not already used is the reason the window existed: a package that will not
start printed its reason there. **So the way of speaking has to exist before
the window can be taken away**, or a broken install fails in silence, which is
worse than the window ever was.

These prove the failure still arrives when there is nowhere to print.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import tell  # noqa: E402


class NoConsole:
    """What `pythonw.exe` looks like from inside Python: nowhere to write.

    Sets the snapshot rather than `sys.stdout`, because that is what the real
    thing is by the time anybody asks. `tell` decides once, at import, before
    it points the streams somewhere safe; a later look at `sys.stdout` would
    answer for the stand-in it installed, not for the machine.
    """

    def __enter__(self):
        self.was = tell._HAS_CONSOLE
        tell._HAS_CONSOLE = False
        return self

    def __exit__(self, *a):
        tell._HAS_CONSOLE = self.was
        return False


def test_a_console_is_noticed_when_there_is_one():
    assert tell.has_a_console() is True


def test_the_streams_are_never_left_as_none():
    """The reason the app died silently on Spenser's machine on 2026-09-03.
    Our own messages check first; uvicorn, every third-party library, and
    Python's own traceback printer do not."""
    assert sys.stdout is not None
    assert sys.stderr is not None


def test_a_console_is_noticed_when_there_is_not():
    with NoConsole():
        assert tell.has_a_console() is False


def test_an_ordinary_line_is_printed_when_somebody_can_see_it(capsys):
    tell.say("Starting Roy R. Fisher 1.2.3.")
    assert "Starting Roy R. Fisher 1.2.3." in capsys.readouterr().out


def test_an_ordinary_line_raises_no_dialog_when_there_is_no_console(monkeypatch):
    """A dialog for every routine line would teach a person to click it away
    without reading, and then the one that mattered would go with it."""
    shown = []
    monkeypatch.setattr(tell, "_dialog", lambda m, i: shown.append(m) or True)
    with NoConsole():
        tell.say("Leave this window open while you work.")
    assert shown == []


def test_a_problem_is_printed_when_there_is_a_console(capsys):
    tell.problem("The app did not start.")
    assert "The app did not start." in capsys.readouterr().out


def test_a_problem_becomes_a_dialog_when_there_is_no_console(monkeypatch):
    """The whole reason this module exists."""
    shown = []
    monkeypatch.setattr(tell, "_dialog", lambda m, i: shown.append(m) or True)
    with NoConsole():
        tell.problem("This package is damaged. Unzip it again.")
    assert shown == ["This package is damaged. Unzip it again."]


def test_a_problem_reaches_the_log_when_even_a_dialog_will_not_come(monkeypatch, tmp_path):
    """Last place left. A machine that can show neither is still a machine
    Spenser can ask for the log."""
    monkeypatch.setenv("RRF_LOG_FILE", str(tmp_path / ".rrf-app.log"))
    monkeypatch.setattr(tell, "_dialog", lambda m, i: False)
    with NoConsole():
        tell.problem("Nowhere to say this out loud.")
    assert "Nowhere to say this out loud." in (tmp_path / ".rrf-app.log").read_text()


def test_nothing_here_ever_raises(monkeypatch):
    """It is the last thing between a failure and silence. It must not be able
    to fail in a way that hides its own message."""
    def explode(*_a, **_k):
        raise RuntimeError("no windowing system")
    monkeypatch.setattr(tell, "_dialog", explode)
    with NoConsole():
        with pytest.raises(RuntimeError):
            tell._dialog("x", 0)          # the stand-in really does raise
    # and the real one swallows it
    monkeypatch.undo()
    with NoConsole():
        tell.problem("This must not raise.")


def test_the_web_server_can_start_with_no_console():
    """The regression Spenser hit on 2026-09-03, an hour after the black
    window was taken away.

    `uvicorn.run` configures its own logging before it serves anything, and
    that configuration reads `ext://sys.stdout`. Under `pythonw.exe` that is
    None, so it raised `ValueError: Unable to configure formatter 'default'`
    and the app died instantly, with no console for the error to appear in.
    Every launch, silently.

    Run in a separate process, because logging configuration is global and a
    test that broke it here would break the suite around it.
    """
    import subprocess
    import textwrap
    code = textwrap.dedent("""
        import sys, os, logging.config
        sys.stdout = None
        sys.stderr = None
        sys.path.insert(0, %r)
        import tell                      # repairs the streams on import
        from uvicorn.config import LOGGING_CONFIG
        logging.config.dictConfig(LOGGING_CONFIG)
        assert tell.has_a_console() is False, "it thinks it can be seen"
        raise SystemExit(0)
    """) % str(Path(__file__).resolve().parents[1] / "server")
    done = subprocess.run([sys.executable, "-c", code],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr

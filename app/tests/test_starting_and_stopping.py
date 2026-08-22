"""Starting and stopping the app should feel like using a program.

Three findings from the audit, all in the black window.

It gave two different instructions for stopping. The window said to press
Control and C; the packaged README said to close the window. Two instructions
for one action, in the two places a first-time user reads.

It printed uvicorn's own INFO lines, including a process id and a bind address,
in a window a person has been told is not a piece of software.

Every ordinary close left `runtime.json` behind naming a dead process. That is
the stale file the housekeeping pass removed by hand, and it was produced by
ordinary use rather than by a crash.

What is deliberately unchanged: the port is still chosen fresh each launch, two
versions still refuse to run at once, and the version still identifies itself.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import startup  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RUN_APP = (ROOT / "app" / "run_app.py").read_text()
PACKAGER = (ROOT / "tools" / "package_windows.py").read_text()


# --- one instruction ------------------------------------------------------
def test_there_is_one_sentence_about_stopping():
    assert startup.STOP_INSTRUCTION == "Close this window to stop the Roy R. Fisher app."


def test_the_window_prints_that_sentence_rather_than_its_own():
    assert "startup.STOP_INSTRUCTION" in RUN_APP


def test_the_packaged_readme_reads_the_same_sentence():
    """Read, not restated, so the two cannot drift apart again."""
    assert "from startup import STOP_INSTRUCTION" in PACKAGER
    assert "STOP_INSTRUCTION +" in PACKAGER


def test_control_c_is_gone_from_what_he_reads():
    assert "Control and C" not in RUN_APP
    assert "Control-C" not in RUN_APP
    assert "Ctrl" not in RUN_APP


def test_he_is_not_pointed_at_a_bookmark():
    """The port changes every launch, so a saved bookmark is dead by morning."""
    assert "rather than from a bookmark" in PACKAGER


# --- a quiet window -------------------------------------------------------
def test_routine_server_chatter_is_off():
    assert 'log_level="warning"' in RUN_APP
    assert "access_log=False" in RUN_APP


def test_the_plain_messages_are_still_printed():
    assert 'print("Starting Roy R. Fisher %s." % version)' in RUN_APP
    assert "startup.failure_report" in RUN_APP


# --- the runtime file -----------------------------------------------------
def test_a_normal_shutdown_forgets_the_port(tmp_path):
    startup.write_runtime(tmp_path, 51234, "0.3.0")
    assert startup.runtime_file(tmp_path).is_file()
    startup.clear_runtime(tmp_path)
    assert not startup.runtime_file(tmp_path).exists()


def test_clearing_is_wired_into_the_way_out():
    """In a finally, so it runs whichever way the server stops."""
    tail = RUN_APP[RUN_APP.index("import uvicorn"):]
    assert "finally:" in tail
    assert "startup.clear_runtime(ROOT)" in tail


def test_clearing_a_file_that_is_not_there_is_not_an_error(tmp_path):
    startup.clear_runtime(tmp_path)          # never ran here
    startup.clear_runtime(tmp_path)          # and again


def test_a_stale_file_left_by_a_crash_is_not_believed(tmp_path, monkeypatch):
    """The next launch probes the port rather than trusting the file."""
    startup.write_runtime(tmp_path, 51234, "0.3.0")
    monkeypatch.setattr(startup, "ask_version", lambda *a, **k: "")
    assert startup.already_running_here(tmp_path, "0.3.0") == 0


def test_a_stale_file_is_replaced_rather_than_appended(tmp_path):
    startup.write_runtime(tmp_path, 51234, "0.2.0")
    startup.write_runtime(tmp_path, 60000, "0.3.0")
    recorded = startup.read_runtime(tmp_path)
    assert recorded["port"] == 60000
    assert recorded["version"] == "0.3.0"


def test_a_live_copy_of_this_version_is_still_found(tmp_path, monkeypatch):
    startup.write_runtime(tmp_path, 51234, "0.3.0")
    monkeypatch.setattr(startup, "ask_version", lambda *a, **k: "0.3.0")
    assert startup.already_running_here(tmp_path, "0.3.0") == 51234


# --- what must not have changed -------------------------------------------
def test_the_port_is_still_asked_for_rather_than_assumed():
    assert "startup.free_port()" in RUN_APP


def test_two_versions_still_refuse_to_run_at_once():
    assert "refuse_if_another_version_runs" in RUN_APP

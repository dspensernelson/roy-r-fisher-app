"""Choosing which part of the log to send, and proving the choice is honest.

On 2026-09-14 at 9:30 the office assistant hit a fault. She was asked for the
log. `Show the log` revealed exactly one file, `~/.rrf-app.log`. The log had
rotated at a megabyte into `~/.rrf-app.log.1` an hour earlier and nothing on
screen said a second file existed. She sent the half that did not hold the
fault and the evidence was gone.

So the unit under test is not "read a file". It is "read both halves, in the
right order, and hand back a piece that cannot be missing the middle".
"""
import datetime
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import logwindow  # noqa: E402


@pytest.fixture
def log_path(tmp_path, monkeypatch):
    path = tmp_path / ".rrf-app.log"
    monkeypatch.setenv("RRF_LOG_FILE", str(path))
    return path


NOW = datetime.datetime(2026, 9, 14, 9, 30, 0)


def stamp(when) -> str:
    return when.isoformat(timespec="seconds")


def line(when, message: str) -> str:
    return "%s %s" % (stamp(when), message)


def days(count):
    return datetime.timedelta(days=count)


def hours(count):
    return datetime.timedelta(hours=count)


# --- nothing written yet ----------------------------------------------------
def test_no_log_at_all_is_answered_and_is_not_an_error(log_path):
    found = logwindow.recent(now=NOW, version="0.7.0")
    assert found["empty"] is True
    assert found["lines"] == 0
    assert "no log" in found["text"].lower()


# --- both halves, oldest first ----------------------------------------------
def test_the_rotated_half_is_read_first_and_the_current_half_second(log_path):
    """The whole reason this module exists. One file was never the log."""
    rotated = log_path.with_name(log_path.name + ".1")
    rotated.write_text(line(NOW - hours(3), "the fault") + "\n")
    log_path.write_text(line(NOW - hours(1), "after the rotation") + "\n")

    found = logwindow.recent(now=NOW, version="0.7.0")
    body = found["text"]
    assert "the fault" in body
    assert "after the rotation" in body
    assert body.index("the fault") < body.index("after the rotation")
    assert str(rotated) in body
    assert str(log_path) in body


def test_a_missing_rotated_half_is_simply_not_read(log_path):
    log_path.write_text(line(NOW - hours(1), "only half of it") + "\n")
    found = logwindow.recent(now=NOW, version="0.7.0")
    assert found["empty"] is False
    assert "only half of it" in found["text"]
    assert str(log_path.with_name(log_path.name + ".1")) not in found["text"]


# --- the two day window -----------------------------------------------------
def test_only_the_last_two_days_come_back(log_path):
    log_path.write_text("\n".join([
        line(NOW - days(9), "far too old"),
        line(NOW - days(3), "still too old"),
        line(NOW - days(1), "inside the window"),
        line(NOW - hours(1), "the fault"),
    ]) + "\n")

    found = logwindow.recent(now=NOW, version="0.7.0")
    text = found["text"]
    assert "far too old" not in text
    assert "still too old" not in text
    assert "inside the window" in text
    assert "the fault" in text
    assert found["lines"] == 2


def test_a_clock_that_jumped_backwards_cannot_punch_a_hole_in_the_middle(log_path):
    """The tail is taken from the boundary, never filtered line by line.

    Her machine's clock is whatever Windows says it is. If it steps back an
    hour mid-morning, filtering each line against the cutoff would silently
    drop the lines written after the step, which is the half holding the
    fault. Everything from the boundary onwards goes, whatever its stamp.
    """
    log_path.write_text("\n".join([
        line(NOW - days(5), "far too old"),
        line(NOW - hours(4), "the boundary"),
        line(NOW - days(40), "written after the clock stepped back"),
        line(NOW - hours(1), "the fault"),
    ]) + "\n")

    found = logwindow.recent(now=NOW, version="0.7.0")
    text = found["text"]
    assert "far too old" not in text
    assert "the boundary" in text
    assert "written after the clock stepped back" in text
    assert "the fault" in text


# --- wrapped messages -------------------------------------------------------
def test_a_line_with_no_stamp_stays_with_the_line_above_it(log_path):
    log_path.write_text("\n".join([
        line(NOW - hours(2), "a message that wraps"),
        "    and here is the rest of it",
        line(NOW - hours(1), "the fault"),
    ]) + "\n")

    found = logwindow.recent(now=NOW, version="0.7.0")
    assert "and here is the rest of it" in found["text"]


def test_a_wrapped_tail_of_an_old_line_does_not_start_the_window(log_path):
    """An unstamped line belongs to the line above it, so it can never be
    the boundary. If it could, a stray continuation of a week-old message
    would drag a week of log into the send."""
    log_path.write_text("\n".join([
        line(NOW - days(6), "a very old message that wraps"),
        "    the rest of the very old one",
        line(NOW - hours(1), "the fault"),
    ]) + "\n")

    found = logwindow.recent(now=NOW, version="0.7.0")
    text = found["text"]
    assert "a very old message that wraps" not in text
    assert "the rest of the very old one" not in text
    assert "the fault" in text


# --- nothing inside the window ----------------------------------------------
def test_nothing_in_two_days_sends_the_last_lines_anyway_and_says_so(log_path):
    log_path.write_text("\n".join(
        line(NOW - days(30) + datetime.timedelta(minutes=i), "old line %d" % i)
        for i in range(logwindow.FALLBACK_LINES + 40)) + "\n")

    found = logwindow.recent(now=NOW, version="0.7.0")
    assert found["lines"] == logwindow.FALLBACK_LINES
    assert "old line 539" in found["text"]
    assert "old line 0" not in found["text"]
    head = found["text"].split("\n\n")[0]
    assert "nothing" in head.lower()
    assert str(logwindow.FALLBACK_LINES) in head


# --- the size ceiling -------------------------------------------------------
def test_too_much_log_is_cut_from_the_oldest_end_and_says_how_many_went(log_path):
    padding = "x" * 400
    wanted = (logwindow.MAX_BYTES // 400) + 800
    log_path.write_text("\n".join(
        line(NOW - hours(20) + datetime.timedelta(seconds=i),
             "line %d %s" % (i, padding))
        for i in range(wanted)) + "\n")

    found = logwindow.recent(now=NOW, version="0.7.0")
    assert len(found["text"].encode("utf-8")) <= logwindow.MAX_BYTES
    assert found["dropped"] > 0
    head = found["text"].split("\n\n")[0]
    assert str(found["dropped"]) in head
    # The newest end is what the fault is at, so that is the end that stays.
    assert "line %d " % (wanted - 1) in found["text"]
    assert "line 0 " not in found["text"]


# --- the header -------------------------------------------------------------
def test_the_header_names_the_version_the_system_the_clock_and_the_counts(log_path):
    log_path.write_text("\n".join([
        line(NOW - hours(5), "first thing"),
        line(NOW - hours(1), "last thing"),
    ]) + "\n")

    import platform
    head = logwindow.recent(now=NOW, version="0.7.0")["text"].split("\n\n")[0]

    assert "0.7.0" in head
    assert platform.system() in head
    assert stamp(NOW) in head                      # the machine's own clock
    assert str(log_path) in head                   # which files were read
    assert "2" in head                             # how many lines
    assert stamp(NOW - hours(5)) in head           # the first stamp
    assert stamp(NOW - hours(1)) in head           # the last stamp


# --- the rule that cost this project two evenings ---------------------------
def test_a_key_shaped_value_cannot_reach_what_is_shown_or_sent(log_path):
    log_path.write_text(
        line(NOW - hours(1), "captions sent key=sk-ant-abcdef1234567890abcdef1234567890")
        + "\n")

    text = logwindow.recent(now=NOW, version="0.7.0")["text"]
    assert "sk-ant-" not in text
    assert "[removed]" in text

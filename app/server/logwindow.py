"""Which part of the log is worth sending, and the header that frames it.

**Why this exists.** On 2026-09-14 at 9:30 the office assistant hit a fault and
was asked for the log. The Settings screen had one control, `Show the log`, and
it revealed exactly one file: `~/.rrf-app.log`. The log had rotated at a
megabyte into `~/.rrf-app.log.1`, and nothing anywhere on screen said that
second file existed. She sent the half without the fault in it. The evidence
was lost and nobody could tell that anything was missing.

So the job here is not "read the log file". It is "read both halves, oldest
first, and hand back a piece that cannot quietly be missing its middle".

**Why the tail is taken from a boundary and never filtered line by line.** Her
clock is whatever Windows says it is, and a clock that steps backwards is an
ordinary event on a machine that syncs time. Filtering each line against a
cutoff would drop every line written after a backwards step, which is a hole in
the middle of the record with nothing on screen to say a hole is there. Finding
the first line at or after the cutoff and then keeping everything after it can
only ever send too much, which is harmless.

**Why an unstamped line belongs to the line above it.** `applog.note` writes one
line per call, but a value inside a call can carry a newline, and an exception
message often does. A continuation line has no stamp of its own. Treating it as
its own record would let half a message arrive without its beginning, or let a
stray continuation of a week-old message become the boundary and drag a week of
log into the send.

**What is not decided here.** Nothing in this module reaches the network, and
nothing in it knows the recipient. It reads two files and returns text.
"""
import datetime
import platform
from pathlib import Path

import applog

# The window the owner approved: the last two days. Long enough to hold
# yesterday afternoon, short enough that a normal send is small.
DAYS = 2

# What to send when nothing at all falls inside the window. An empty send would
# be the same failure in a new costume: a screen that says it worked while the
# owner receives nothing worth reading.
FALLBACK_LINES = 500

# The ceiling on one send, the whole payload and not just the body. The same
# number `applog.MAX_BYTES` rotates at, pointed at rather than typed again, so
# a change to one cannot leave the other behind. This project has a recorded,
# repeating defect where a value is copied instead of pointed at.
MAX_BYTES = applog.MAX_BYTES

# Room reserved for the header, which is written before the body is cut and
# therefore cannot be measured first without writing it twice. A header is a
# dozen short lines plus two file paths; two kilobytes is generous.
HEADER_ROOM = 2000

# `applog.note` writes `datetime.now().isoformat(timespec="seconds")`, which is
# exactly nineteen characters and carries no time zone, because the machine's
# own clock is the only clock this app has ever known about.
STAMP_CHARS = 19
STAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"

ROTATED_SUFFIX = ".1"


def files_in_order():
    """The log files that exist, oldest first, rotated half before current.

    An empty list means nothing has ever been written. That is an answer, not
    a failure: a machine that has never run the app has no log and saying so
    is the honest thing to send.
    """
    current = applog.log_file()
    rotated = current.with_name(current.name + ROTATED_SUFFIX)
    return [path for path in (rotated, current) if path.is_file()]


def read_stream():
    """Every line of both halves as one list, oldest first, with the paths read.

    Read with `errors="replace"` rather than strictly. A log that cannot be
    decoded is still the only evidence there is, and refusing to send it
    because one byte is wrong would be this same defect a second time.
    """
    lines = []
    read = []
    for path in files_in_order():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        read.append(path)
        lines.extend(text.splitlines())
    return lines, read


def stamp_of(line: str):
    """The time at the head of a line, or None when it carries none.

    None is the answer for a continuation line, and the caller treats it as
    part of the line above rather than as a record of its own.
    """
    head = line[:STAMP_CHARS]
    if len(head) < STAMP_CHARS:
        return None
    try:
        return datetime.datetime.strptime(head, STAMP_FORMAT)
    except ValueError:
        return None


def boundary(lines, cutoff):
    """Where the send starts: the first line stamped at or after the cutoff.

    Returns -1 when no line is inside the window at all. Unstamped lines are
    skipped rather than considered, because they belong to the line above.
    """
    for index, line in enumerate(lines):
        when = stamp_of(line)
        if when is not None and when >= cutoff:
            return index
    return -1


def _first_stamped(lines) -> int:
    """The first line that opens a record rather than continuing one."""
    for index, line in enumerate(lines):
        if stamp_of(line) is not None:
            return index
    return 0


def tail(lines, count):
    """The last `count` lines, starting at a line that opens a record.

    Starting mid-message would hand the owner half a sentence with no way to
    know the rest existed.
    """
    kept = lines[-count:] if count < len(lines) else list(lines)
    return kept[_first_stamped(kept):]


def cut_to_fit(lines, ceiling):
    """Drop the oldest lines until the body fits. Returns the lines and the count.

    The oldest end goes because the newest end is where the fault is. A send
    that dropped the newest lines to stay small would be arithmetically
    correct and useless.
    """
    kept = list(lines)
    dropped = 0
    while kept and len("\n".join(kept).encode("utf-8")) > ceiling:
        # Drop a chunk at a time rather than one line, so a megabyte of log
        # does not cost a megabyte of string joins.
        step = max(1, len(kept) // 20)
        kept = kept[step:]
        dropped += step
    if kept:
        start = _first_stamped(kept)
        dropped += start
        kept = kept[start:]
    return kept, dropped


def _stamp_text(when) -> str:
    return when.isoformat(timespec="seconds")


def header(version, now, read, count, first, last, note) -> str:
    """The facts the owner needs before he reads a single line.

    Which files were read is in here on purpose. The fault this whole feature
    answers was a missing second file that nothing on screen mentioned.
    """
    lines = [
        "Roy R. Fisher, the last %d days of the log" % DAYS,
        "App version: %s" % (version or "unknown"),
        "Operating system: %s" % platform.system(),
        "This computer's clock: %s" % _stamp_text(now),
        "Read from: %s" % (", ".join(str(path) for path in read)
                           if read else "nothing, no log file has been written "
                                        "on this computer yet"),
        "Lines: %d" % count,
    ]
    if first is not None:
        lines.append("First line: %s" % _stamp_text(first))
    if last is not None:
        lines.append("Last line: %s" % _stamp_text(last))
    if note:
        lines.append(note)
    return "\n".join(lines)


def recent(now=None, version="") -> dict:
    """What to show on screen and what to send. Never raises.

    `version` is passed in rather than worked out here, because `main.py`
    already computes the program folder once and a second copy of that
    expression is exactly the defect this project keeps repeating.

    Returns `text`, the whole payload including its header; `lines`, how many
    log lines are in it; `dropped`, how many were left out for size; and
    `empty`, which is true only when no log file exists at all.

    **Everything is passed through `applog.redact` before it leaves this
    function**, so what the screen shows is byte for byte what gets sent. The
    log is written redacted already, and this is that rule applied a second
    time to lines written before a redaction rule existed. `sendlog` applies
    it a third time on the way out.
    """
    if now is None:
        now = datetime.datetime.now()

    lines, read = read_stream()
    if not read:
        return {"text": header(version, now, [], 0, None, None, ""),
                "lines": 0, "dropped": 0, "empty": True}

    note = ""
    start = boundary(lines, now - datetime.timedelta(days=DAYS))
    if start < 0:
        kept = tail(lines, FALLBACK_LINES)
        note = ("Note: nothing was written in the last %d days, so this is the "
                "last %d lines instead." % (DAYS, FALLBACK_LINES))
    else:
        kept = lines[start:]

    kept, dropped = cut_to_fit(kept, MAX_BYTES - HEADER_ROOM)
    if dropped:
        note = ("Note: too long to send whole, so the oldest %d lines were "
                "left out." % dropped)

    stamps = [stamp_of(line) for line in kept]
    stamps = [when for when in stamps if when is not None]
    first = stamps[0] if stamps else None
    last = stamps[-1] if stamps else None

    text = header(version, now, read, len(kept), first, last, note)
    if kept:
        text = text + "\n\n" + "\n".join(kept)
    text = applog.redact(text)

    # A last guard rather than a trusted calculation. If a header ever grew
    # past its room, the ceiling still holds and the newest end is what stays.
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_BYTES:
        text = encoded[-MAX_BYTES:].decode("utf-8", errors="replace")

    return {"text": text, "lines": len(kept), "dropped": dropped,
            "empty": False}

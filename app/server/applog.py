"""A written record of what the app did, kept on the machine it ran on.

Nothing in this codebase wrote anything down before this. `run_app.py` sets
`log_level="warning"` and `access_log=False` on purpose, because uvicorn's own
console noise does not belong in a window a person has been told is not a
piece of software. Several places swallow an exception on purpose too, with a
comment saying diagnostic bookkeeping must never take the app down, and no
record kept at all.

Both are still true after this module. Nothing new appears in the console
window. What changes is that a second, separate record now exists, in a file,
so that a screen that sits and says nothing leaves something to look at
afterward. `Settings` grows a `Show the log` button so it can be found without
typing a path.

`note` never raises. A logger that can take the app down is worse than no
logger, and every caller here already runs inside code that must survive a
failure.

One line per call, plain text, one fact per key. Not JSON: a person opening
this file to read it, not a program, is the reader who matters most.
"""
import datetime
import os
import re
from pathlib import Path

LOG_NAME = ".rrf-app.log"
MAX_BYTES = 1_000_000

# What a value must never contain, checked before it is written and not
# after. The app's own key is never printed, logged, or sent anywhere but the
# server; this is that rule enforced in the one place logging could quietly
# break it.
_KEY_SHAPED = re.compile(r"sk-ant-[A-Za-z0-9_-]+|[A-Za-z0-9_-]{40,}")


def log_file() -> Path:
    """Home folder on both Mac and Windows. RRF_LOG_FILE overrides, for
    tests, the same way RRF_KEY_FILE already does for the key."""
    override = os.environ.get("RRF_LOG_FILE")
    return Path(override) if override else Path.home() / LOG_NAME


def redact(text: str) -> str:
    """Replace anything shaped like a key or a long secret with a marker,
    rather than trying to know every key format there will ever be."""
    return _KEY_SHAPED.sub("[removed]", text)


def _rotate(path: Path) -> None:
    try:
        if path.is_file() and path.stat().st_size >= MAX_BYTES:
            previous = path.with_name(path.name + ".1")
            try:
                previous.unlink()
            except OSError:
                pass
            path.rename(previous)
    except OSError:
        pass


def note(message: str, **fields) -> None:
    """Write one line: a timestamp, the message, then key=value pairs.

    Never raises. Every field is passed through `redact` before it is
    written, whatever its source, because a caller three modules away adding
    a new field is exactly how a key would otherwise slip in unnoticed.
    """
    try:
        path = log_file()
        _rotate(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().isoformat(timespec="seconds")
        parts = [stamp, redact(str(message))]
        for key, value in fields.items():
            parts.append("%s=%s" % (key, redact(str(value))))
        line = " ".join(parts) + "\n"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
    except Exception:
        pass

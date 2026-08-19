"""Which version of the app last actually started, kept for Spenser to read.

Its own file, deliberately not a corner of `~/.rrf-app.json`. That file is
written every time Mark picks a jobs folder or changes his active job list, so
it is the file most likely to be caught half-written by a crash. Putting the
crash-recovery record inside the file most likely to be damaged by a crash is
backwards, and "one fewer file to look after" was the only argument for it.

This module stores and reads. It does not decide when a version has earned the
record. The rule, from the plan, is that a version counts as started only when
the running server answered with its own exact version string and was still
alive twenty seconds later, and the timer that enforces that belongs to Task 3
along with the version endpoint and the launcher. Nothing here starts a timer,
opens a socket, or rolls anything back: rollback stays a person closing one
folder and double-clicking another.
"""
import os
from pathlib import Path

import state

STORE_NAME = ".rrf-app-version.json"

LAST_GOOD_KEY = "last_good"
QUALIFIED_AT_KEY = "qualified_at"


def store_file() -> Path:
    """Home folder on both Mac and Windows. RRF_VERSION_FILE overrides, for
    tests, the same way RRF_KEY_FILE already does for the key."""
    override = os.environ.get("RRF_VERSION_FILE")
    return Path(override) if override else Path.home() / STORE_NAME


def read() -> dict:
    """The record, or {} when nothing has qualified yet.

    Raises state.StateUnreadable when the file is there and damaged, the same
    as every other app-owned file. A damaged record answered as "no version has
    ever started" would be a lie told at exactly the moment somebody is trying
    to work out what broke.
    """
    return state.without_schema(state.read_json(store_file()))


def last_good() -> str:
    """The version string, or empty. Never a guess."""
    value = read().get(LAST_GOOD_KEY, "")
    return value if isinstance(value, str) else ""


def qualified_at() -> str:
    """When that version earned the record, as the caller stamped it."""
    value = read().get(QUALIFIED_AT_KEY, "")
    return value if isinstance(value, str) else ""


def record(version: str, when: str) -> None:
    """Remember that this version started successfully at this moment.

    Both values are given by the caller rather than read from a clock here, so
    the moment recorded is the moment the caller actually observed, and so a
    test can state it instead of racing one.
    """
    version = str(version).strip()
    if not version:
        raise ValueError("a version string is required")
    when = str(when).strip()
    if not when:
        raise ValueError("a timestamp is required")
    state.write_json(store_file(), {LAST_GOOD_KEY: version,
                                    QUALIFIED_AT_KEY: when})

"""One guard, so a reset and a write can never run at the same time.

The demo reset renames whole folders out from under the app. Any write that
happened to be in flight would land in a folder that is being moved, or in
the folder that replaces it, and neither is recoverable by looking at the
result afterwards.

One lock and two counters, in one module, rather than a flag on each screen.
A disabled button is courtesy, not protection: the server refuses on its own,
and the tests call the routes directly with the guard held to prove it.

threading.Lock is the right primitive because the web server answers plain
`def` endpoints on a pool of threads.
"""
import threading
from contextlib import contextmanager

# What the caller is told, and what the screens repeat back word for word.
RESET_REFUSED = "Another operation is in progress. Nothing was reset."
WRITE_REFUSED = "The demo is being reset. Nothing was changed."


class Busy(Exception):
    """Somebody else holds the floor. Carries the message for the caller."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


_lock = threading.Lock()
_writers = 0
_resetting = False


def check_not_resetting() -> None:
    """Refuse now if a reset holds the floor, before doing any other work.

    `writing()` already refuses, but a route that validates before it writes
    would answer the validation first and tell Mark his captions need review
    while the demo folders are being replaced underneath him. This lets such a
    route refuse for the real reason, at the top, without holding the lock
    through a long build.
    """
    with _lock:
        if _resetting:
            raise Busy(WRITE_REFUSED)


@contextmanager
def writing():
    """Held by every route that writes a job file or a setting."""
    global _writers
    with _lock:
        if _resetting:
            raise Busy(WRITE_REFUSED)
        _writers += 1
    try:
        yield
    finally:
        with _lock:
            _writers -= 1


@contextmanager
def resetting():
    """Held by the demo reset, and nothing else."""
    global _resetting
    with _lock:
        if _writers:
            raise Busy(RESET_REFUSED)
        if _resetting:
            raise Busy(RESET_REFUSED)
        _resetting = True
    try:
        yield
    finally:
        with _lock:
            _resetting = False


def state() -> dict:
    """For tests. Never exposed over the API."""
    with _lock:
        return {"writers": _writers, "resetting": _resetting}

"""How far a caption run has got, while it is still going.

A run of sixty-one photographs is divided into requests and takes real
minutes. The screen showed a thin indeterminate bar in a corner and nothing
else, so the app knew it was on request one of two and did not say. Worse, the
photographs already captioned and already saved kept showing an empty caption
box until the whole run finished, which made finished work look lost.

The run itself is one synchronous request, so this is where the two halves
meet: the run writes its position here as it goes, and the screen asks for it
on a timer. Nothing here is durable and nothing here is authoritative. The
manifest on disk is the truth about captions; this is only a progress light.

Keyed by job name, holding one entry per job, and cleared when the run ends.
A dictionary guarded by a lock rather than a file: it is worthless a second
after the run finishes, and writing it to disk would put a temporary fact
somewhere permanent.
"""
import threading

_lock = threading.Lock()
_runs = {}


def start(job: str, total: int, requests: int) -> None:
    """A run is beginning. Replaces anything left by an earlier one."""
    with _lock:
        _runs[str(job)] = {"running": True, "request": 0, "requests": int(requests),
                           "captioned": 0, "total": int(total)}


def advance(job: str, request: int, captioned: int) -> None:
    """One request has finished and its captions are saved."""
    with _lock:
        found = _runs.get(str(job))
        if found is None:
            return
        found["request"] = int(request)
        found["captioned"] = int(captioned)


def finish(job: str) -> None:
    """The run is over, however it ended. The screen stops asking."""
    with _lock:
        _runs.pop(str(job), None)


def read(job: str) -> dict:
    """Where this job's run has got to, or a plain not-running answer.

    Never invents a position. A job with no run reports zeros, which is what
    the screen shows before the first request comes back and after the last
    one does.
    """
    with _lock:
        found = _runs.get(str(job))
        if found is None:
            return {"running": False, "request": 0, "requests": 0,
                    "captioned": 0, "total": 0}
        return dict(found)


# ------------------------------------------------- how far a read has got --
# A second keyspace, not a second meaning for the first.
#
# `_runs` holds one entry per job and `start` replaces it, so a photo-list read
# beginning during a caption run would wipe that run's position. The caption
# poller refetches the manifest while a run is going
# (`PhotosScreen.jsx:111`), so the two really do overlap and this is not a
# theoretical collision.
#
# Its field names are caption vocabulary too. `requests` and `captioned` mean
# nothing to a read, and reusing them would make the payload lie.
#
# `updates.py` set the precedent on 2026-08-28: it copied this module's shape
# for a second concern rather than overloading the one dictionary. Same choice
# here, same reason.
_reads = {}


def read_start(job: str, total: int) -> None:
    """A read of this job's photographs is beginning."""
    with _lock:
        _reads[str(job)] = {"reading": True, "done": 0, "total": int(total)}


def read_advance(job: str, done: int, total: int) -> None:
    """How far it has got. A no-op for a job that is not reading, so a late
    tick after the end cannot bring the light back on."""
    with _lock:
        found = _reads.get(str(job))
        if found is None:
            return
        found["done"] = int(done)
        found["total"] = int(total)


def read_finish(job: str) -> None:
    """However the read ended, including badly. A light left on leaves the
    screen polling for ever."""
    with _lock:
        _reads.pop(str(job), None)


def read_state(job: str) -> dict:
    """What the screen shows while it waits, or all zeroes.

    A copy, so a caller cannot reach in and change what the reader is
    reporting about itself.
    """
    with _lock:
        found = _reads.get(str(job))
        if found is None:
            return {"reading": False, "done": 0, "total": 0}
        return dict(found)

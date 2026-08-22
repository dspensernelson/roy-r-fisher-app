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

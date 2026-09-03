"""Getting the app running, and refusing to when that would be wrong.

Standard library only, like packaging.py and for the same reason: all of this
runs before uvicorn is imported, so it still works in a package whose wheels
are the thing that went missing.

Three decisions live here, and each one was a defect in the first design.

The port is asked for rather than assumed. Binding 0 lets the operating system
pick a free one, and the number is written into this version's own
`runtime.json`. Port 8000 was hardcoded, which made two installed versions
indistinguishable; walking up from 8000 to the first free port was the other
candidate and is worse, because it starts a second copy rather than finding the
first, and it has no terminating condition if a security product answers on
every port it tries.

Only this exact version may answer for this folder. The old check asked "is
anything alive on 8000" and treated yes as success. That meant double-clicking
v1 while v2 was running opened v2, and the reverse, so an upgrade and a
rollback both looked like they had worked while showing the wrong app. The
probe now asks `/api/version` and compares the string.

Two versions never run at once. `busy.py` is a threading lock, so it guards
writes inside one process and nothing across two, and both processes would
write the same files in the home folder. Before starting, this looks at the
sibling version folders beside its own and refuses if one of them is alive.
"""
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RUNTIME_NAME = "runtime.json"

HOST = "127.0.0.1"

# One sentence about stopping the app, in one place, so the terminal and the
# packaged README cannot drift apart. They used to disagree: the window said to
# press Control and C and the README said to close the window, which is two
# instructions for one action in the two places a first-time user reads.
STOP_INSTRUCTION = ("To stop the Roy R. Fisher app, open Settings and "
                    "choose Close the app.")
# Changed 2026-09-03, when the black console window went. It used to say
# "Close this window", which was the only way to stop the app and is now
# not true: on Windows there is no window at all. One sentence, read by the
# packaged readme and by the console on the Mac, so the two cannot drift.

# Loopback only, never 0.0.0.0. Windows Defender Firewall generally does not
# prompt for a loopback-only bind, and an unsigned launcher opening a listening
# socket is already a recognisable shape to endpoint protection. Recorded here
# so a later change does not quietly give that away.
BIND_HOST = "127.0.0.1"

PROBE_TIMEOUT = 1.5
START_TIMEOUT = 30.0


class StartupRefused(Exception):
    """A reason not to start, already written the way Mark should read it."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# ------------------------------------------------------------ this folder ---
def runtime_file(root: Path) -> Path:
    """Inside this version's own `program` folder.

    Deliberately not in the home folder: it describes one installed copy, and
    two installed copies must be able to disagree about it. Deliberately not in
    the manifest either, because it changes every run. And deliberately not at
    the top of the unzipped folder, which is the part Mark looks at.

    Takes either the version folder or the `program` folder inside it, so the
    sibling scan can hand it a folder it has only just discovered.
    """
    import packaging          # standard library only, same as this module
    return packaging.program_dir(root) / RUNTIME_NAME


def clear_runtime(root: Path) -> None:
    """Forget the port this copy bound, on the way out of a normal shutdown.

    The file describes a running app. Left behind it describes one that is not
    running, and that is exactly the stale file the audit found: every ordinary
    close produced one, naming a dead process.

    Never raises. Failing to tidy up must not turn a clean exit into an error,
    and a leftover file is already safe: `already_running_here` probes the port
    and only trusts it when this same version answers, so a crash that skips
    this is handled by the next launch rather than by this line.
    """
    try:
        runtime_file(root).unlink()
    except (OSError, FileNotFoundError):
        pass


def read_runtime(root: Path) -> dict:
    """What this folder last recorded, or {} when it has never started.

    Never raises. A folder that has never run has no file, and a file we cannot
    read tells us nothing worth acting on, so both mean "nothing known".
    """
    try:
        data = json.loads(runtime_file(root).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_runtime(root: Path, port: int, version: str) -> None:
    """Record the port this copy bound, and which version bound it.

    Written after the manifest check has already passed, and outside the
    immutable set, so writing it can never invalidate the package.
    """
    payload = {"port": int(port), "version": str(version), "pid": os.getpid()}
    path = runtime_file(root)
    temp = path.with_name("%s.%d.writing" % (path.name, os.getpid()))
    try:
        temp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(str(temp), str(path))
    except Exception:
        try:
            if temp.exists():
                temp.unlink()
        except OSError:
            pass
        raise


# ------------------------------------------------------------- the probe ----
def ask_version(port: int, timeout: float = PROBE_TIMEOUT) -> str:
    """The version answering on this port, or empty.

    Empty covers every way this can fail to be our app: nothing listening, a
    connection refused, something that answers but not with JSON, something
    that answers with JSON that has no version in it. All of those mean the
    same thing to every caller here, which is "not us", and none of them may
    ever be treated as success.
    """
    url = "http://%s:%d/api/version" % (HOST, int(port))
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, OSError, ValueError, TypeError):
        return ""
    if not isinstance(body, dict):
        return ""
    found = body.get("version", "")
    return found if isinstance(found, str) else ""


def free_port() -> int:
    """Ask the operating system for one, rather than guessing at 8000.

    Bound and closed here, then bound again by the server a moment later. The
    gap is a real race in principle and not one in practice on a machine with
    one user and one app, and closing it would mean handing uvicorn a socket,
    which is a great deal of machinery for a risk that does not exist here.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((BIND_HOST, 0))
        return int(sock.getsockname()[1])


# ------------------------------------------------------ the sibling check ---
def sibling_folders(root: Path):
    """The other installed versions sitting beside this one.

    Mark keeps the previous folder until the new one has worked once, which is
    the whole rollback mechanism, so siblings are expected rather than odd.
    """
    root = Path(root).resolve()
    parent = root.parent
    try:
        entries = sorted(p for p in parent.iterdir() if p.is_dir())
    except OSError:
        return []
    return [p for p in entries if p.resolve() != root and runtime_file(p).is_file()]


def running_sibling(root: Path):
    """The first sibling that is actually alive, as (folder, version).

    A sibling that has a runtime.json but answers nothing has simply been run
    before and closed. That is the ordinary case after a rollback and it is not
    a reason to refuse.
    """
    for folder in sibling_folders(root):
        recorded = read_runtime(folder)
        port = recorded.get("port")
        if not isinstance(port, int):
            continue
        answering = ask_version(port)
        if answering:
            return folder, answering
    return None


def refuse_if_another_version_runs(root: Path) -> None:
    """Two copies must never write the home folder at the same time."""
    found = running_sibling(root)
    if found is None:
        return
    folder, version = found
    raise StartupRefused(
        "Roy R. Fisher %s is already running, from:\n"
        "    %s\n"
        "Close that window first, then start this one again.\n"
        "Only one version can run at a time."
        % (version, folder))


def already_running_here(root: Path, version: str) -> int:
    """The port this same version is already answering on, or 0.

    Both halves matter. A port recorded by this folder is not enough, because
    something else may have taken it since; and something answering is not
    enough either, because it may be another program or another version. Only
    our own version string on our own recorded port counts.
    """
    recorded = read_runtime(root)
    port = recorded.get("port")
    if not isinstance(port, int):
        return 0
    return port if ask_version(port) == version else 0


# -------------------------------------------------------- waiting to be up --
def wait_until_answering(port: int, version: str, timeout: float = START_TIMEOUT,
                         sleep=time.sleep, now=time.monotonic) -> bool:
    """Poll until our own version answers, or give up.

    The browser used to open on a one second timer, which is a guess that shows
    Mark a dead page whenever the machine is slow. This waits for a real answer
    and for the right one.
    """
    deadline = now() + timeout
    while now() < deadline:
        if ask_version(port, timeout=0.5) == version:
            return True
        sleep(0.25)
    return False


def failure_report(root: Path, port: int, version: str) -> str:
    """What went wrong, what was tried, and what to do about it.

    Printed instead of a traceback, and the `.bat` pauses afterwards so the
    window stays open long enough to read it.
    """
    return (
        "Roy R. Fisher %s did not finish starting.\n"
        "\n"
        "  Folder: %s\n"
        "  Port:   %d\n"
        "  Waited: %d seconds for the app to answer\n"
        "\n"
        "Close this window and try again. If it happens twice, send Spenser\n"
        "this whole window and do not delete the folder."
        % (version or "(unknown version)", Path(root), int(port), int(START_TIMEOUT)))

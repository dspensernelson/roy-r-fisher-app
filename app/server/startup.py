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
write the same files in the home folder. Before starting, this looks at this
folder and at the sibling version folders beside it, and stops whatever is
alive before carrying on.

It used to refuse instead, and tell Mark to close the running app's window.
There has been no window since 0.6.5 and the tab it opened may be long gone, so
that was an instruction he could not follow, with nothing else on offer but
Task Manager. Stopping the old copy is done over the app's own `Close the app`
route, the same one the Settings screen posts to, so there is one way to stop
the app rather than two.
"""
import json
import os
import socket
import sys
import threading
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

# The app's own way of being asked to stop. Owned here and read by the route in
# `main.py`, so the launcher and the server cannot come to disagree about it.
# The Settings screen posts to the same path from the browser.
CLOSE_PATH = "/api/close"

# How long a copy gets to go away after it has been asked to.
#
# The copy being stopped waits for its own writes to finish first, which is
# bounded at 30 seconds, and then pauses a moment so its screen can say what
# happened. 40 leaves room for both and for a slow machine. Those two numbers
# are deliberately not read from `busy` and `main` here: the copy being stopped
# is a different process, quite possibly an older build with different numbers,
# so its constants are not ours to reach into. Waiting a little too long costs
# seconds in a case that is already going wrong. Giving up too early would call
# a working close a failure and send him to Task Manager for nothing.
STOP_TIMEOUT = 40.0


# ------------------------------------------------- the loading page's hand ---
# How the loading page says it got here, so the launcher opens one tab and not
# two.
#
# The page already asks this app whether it is up, every half second, from a
# file on disk. That asking is now the message: the route below is hit only by
# that page, so the app hearing it is proof the page reached it and is about to
# move itself over. Nothing is sent back that the page reads; the answer is
# opaque to it, and arriving at all is the whole content.
#
# An event in this process rather than a second endpoint or a file, because the
# launcher thread that decides whether to open a browser is a thread of the
# server process. `uvicorn.run` imports `main` here, so `main` and `run_app`
# hold this same module and this same flag.
#
# It is one way only, and deliberately. Set means the page spoke, which can
# only be true. Clear means nothing has been heard, which covers the page being
# blocked, the browser being slow, and there being no page at all, and every
# one of those has the same right answer: open the app. The failure that costs
# nothing is a spare tab. The failure that cost an evening on 2026-09-14 is an
# app running with nobody looking at it.
LOADING_PAGE_PATH = "/api/loading-page"

_loading_page = threading.Event()


def the_loading_page_arrived() -> None:
    """Called by the route. The page reached us and is about to hand over."""
    _loading_page.set()


def wait_for_the_loading_page(seconds: float) -> bool:
    """True if the page has spoken, waiting up to `seconds` for it to.

    False is not a failure and never says anything went wrong. It says nobody
    has told us anything, and the caller's answer to that is to open the app
    itself.
    """
    return _loading_page.wait(float(seconds))


def forget_the_loading_page() -> None:
    """Only the tests need this. The flag lasts exactly one run of the app."""
    _loading_page.clear()


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


def answering_at(folder: Path):
    """What is alive in this folder right now, as (version, port), or None.

    The one place that asks the question, so nothing else rebuilds it. Both
    halves matter. A port recorded by a folder is not enough, because something
    else may have taken it since; and something answering is not enough either,
    because it may be another program. Only our app's own answer on that
    folder's own recorded port counts.
    """
    recorded = read_runtime(folder)
    port = recorded.get("port")
    if not isinstance(port, int):
        return None
    answering = ask_version(port)
    return (answering, port) if answering else None


def running_sibling(root: Path):
    """The first sibling that is actually alive, as (folder, version).

    A sibling that has a runtime.json but answers nothing has simply been run
    before and closed. That is the ordinary case after a rollback.
    """
    for folder in sibling_folders(root):
        found = answering_at(folder)
        if found:
            return folder, found[0]
    return None


def copies_running(root: Path):
    """Every copy of the app alive right now, as (folder, version, port).

    This folder first, then the ones installed beside it. Both belong in one
    list because both are the same fact to the launcher: something is holding
    the home folder and has to go before this copy starts.

    This folder counts whatever version it answers with, which is the point.
    Four builds on 2026-09-14 all called themselves 0.7.0, so a newly unpacked
    build is not something `/api/version` can tell from a two-hour-old one, and
    an app that cannot tell them apart may not claim the right one is running.
    """
    found = []
    here = answering_at(root)
    if here:
        found.append((Path(root).resolve(), here[0], here[1]))
    for folder in sibling_folders(root):
        alive = answering_at(folder)
        if alive:
            found.append((folder, alive[0], alive[1]))
    return found


def already_running_here(root: Path, version: str) -> int:
    """The port this same version is already answering on, or 0.

    Kept for the installer, which asks a narrower question than the launcher:
    it wants to know whether the copy it is about to overwrite is this exact
    version. The launcher no longer asks it, because the version number is not
    enough to tell one build from another.
    """
    found = answering_at(root)
    return found[1] if found and found[0] == version else 0


# --------------------------------------------------- stopping the old one ---
def ask_it_to_stop(port: int, timeout: float = PROBE_TIMEOUT) -> bool:
    """Ask the copy on this port to close itself. True if it took the request.

    The same route the `Close the app` button on the Settings screen posts to,
    rather than a second way of stopping the app invented here. It lets the
    running copy finish whatever it is writing and go on its own terms, which
    is the whole reason that route exists.

    False covers every way this can fail: nothing listening, a copy too old to
    have the route, something that is not our app. None of those may ever be
    treated as a yes, because the caller has to be able to say truthfully that
    the old copy is gone.
    """
    url = "http://%s:%d%s" % (HOST, int(port), CLOSE_PATH)
    request = urllib.request.Request(url, data=b"", method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, OSError, ValueError, TypeError):
        return False


def wait_until_it_stops(port: int, version: str, timeout: float = STOP_TIMEOUT,
                        sleep=time.sleep, now=time.monotonic) -> bool:
    """Poll until that copy stops answering, or give up.

    Polled rather than slept through. A fixed sleep is a guess, and it is
    either too long on a fast machine or too short on Mark's, and being too
    short here means starting a second copy beside a live one.
    """
    deadline = now() + timeout
    while now() < deadline:
        if ask_version(port, timeout=0.5) != version:
            return True
        sleep(0.25)
    return False


# What to do after the restart, when nothing else has worked. The launcher's
# answer, and the default, because that is where this message was born.
BACK_TO_THE_APP = "double-click the Roy R. Fisher icon again"


def would_not_stop(folder: Path, version: str, port: int,
                   next_step: str = None) -> str:
    """What to say when a copy will not go, and what he can do about it.

    Everything this copy could do has already been done by the time this is
    read, and the message says so before it asks him for anything. Task Manager
    is named last, after the thing that always works, because finding a process
    in a list is not something to ask an appraiser to do first.

    `next_step` is the one line that differs between the two places this is
    read. Somebody who double-clicked the icon is sent back to the icon;
    somebody who unzipped a package and ran the installer is sent back to the
    installer. Everything else is the same message, in one place, rather than
    two messages that drift.
    """
    return (
        "Roy R. Fisher %s is still running and would not stop.\n"
        "\n"
        "  Folder: %s\n"
        "  Port:   %d\n"
        "\n"
        "This copy asked it to close and then waited %d seconds. It is still\n"
        "answering, so nothing was changed.\n"
        "\n"
        "Restart the computer, then\n"
        "%s.\n"
        "\n"
        "If you would rather not restart: hold Control, Shift and Escape\n"
        "together to open Task Manager, find pythonw.exe in the list, and\n"
        "choose End task."
        % (version or "(unknown version)", Path(folder), int(port),
           int(STOP_TIMEOUT), next_step or BACK_TO_THE_APP))


def stop_the_running_copies(copies, say=None, timeout: float = STOP_TIMEOUT,
                            sleep=time.sleep, now=time.monotonic,
                            next_step: str = None) -> None:
    """Stop every copy that is running, so this one can take over.

    Raises `StartupRefused` only once asking has been tried and has not worked,
    which is the only honest moment to refuse: before that, nothing has been
    attempted, and a refusal with nothing attempted is what 0.7.0 did.

    `say` is how this reaches the screen. Stopping the old copy takes a few
    seconds in which nothing else is happening, and silence at the very first
    click reads as the click having failed.

    `next_step` is passed through to the message, because the installer calls
    this too and it got here by a different route. See `would_not_stop`.
    """
    for folder, version, port in copies:
        if say:
            say("Roy R. Fisher %s is already open. Closing it." % version)
        ask_it_to_stop(port)
        if say:
            say("Waiting for it to close.")
        if not wait_until_it_stops(port, version, timeout=timeout,
                                   sleep=sleep, now=now):
            raise StartupRefused(
                would_not_stop(folder, version, port, next_step))
        if say:
            say("It has closed.")


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

    Printed instead of a traceback. It reaches Mark as a dialog box, because
    `tell.problem` finds no console to print to, so it may not name a window:
    it used to say "Close this window and try again", and there has been no
    window since 0.6.5.
    """
    return (
        "Roy R. Fisher %s did not finish starting.\n"
        "\n"
        "  Folder: %s\n"
        "  Port:   %d\n"
        "  Waited: %d seconds for the app to answer\n"
        "\n"
        "Start Roy R. Fisher again. If it happens twice, send Spenser this\n"
        "message and do not delete the folder."
        % (version or "(unknown version)", Path(root), int(port), int(START_TIMEOUT)))

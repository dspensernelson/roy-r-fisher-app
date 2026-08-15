"""Walking his own folders, inside the app's own page.

The app's page is already in front of him, so a list drawn here cannot end up
behind the browser the way the computer's own folder window did. Folders
only: a loose file is never offered as somewhere to go, and nothing here
guesses what a folder is for.

Pure standard library, no Mac-only call. The one platform branch is for
Windows drive letters, which macOS does not have.
"""
import os
import string
import sys
from pathlib import Path

# Where "up" leads when there is nowhere above a drive. The browser asks for
# this by name and gets the list of drives back.
DRIVES = "\x00drives"


def on_windows() -> bool:
    return sys.platform.startswith("win")


def drives() -> list:
    """Every local drive that actually answers, one probe at a time.

    os.listdrives() only exists from Python 3.12 and nobody has checked what
    is on Mark's machine, so this asks each letter itself. Each probe is
    caught on its own: a drive that is empty, locked, or a card reader with
    nothing in it drops out of the list instead of breaking the screen.
    """
    found = []
    for letter in string.ascii_uppercase:
        root = "%s:\\" % letter
        try:
            if Path(root).is_dir():
                found.append(root)
        except OSError:
            continue
    return found


def _breadcrumbs(path: Path) -> list:
    """Every step from the top down to here, each one clickable."""
    parts = []
    current = path
    while True:
        parts.append({"label": current.name or str(current), "path": str(current)})
        if current.parent == current:
            break
        current = current.parent
    parts.reverse()
    if on_windows():
        parts.insert(0, {"label": "This PC", "path": DRIVES})
    return parts


def home() -> str:
    return str(Path.home())


def listing(where: str = "") -> dict:
    """What is directly inside this folder, read now.

    Never lists files, never follows a name it has not resolved, and reports
    a folder it cannot open as unreadable rather than as empty. "Locked" and
    "nothing in it" are different answers and he is told which one it is.
    """
    answer = {"path": "", "label": "", "parent": None, "breadcrumbs": [],
              "folders": [], "readable": True, "is_drive_list": False,
              "loose_files": 0, "message": ""}

    if where == DRIVES:
        answer.update(path=DRIVES, label="This PC", is_drive_list=True,
                      breadcrumbs=[{"label": "This PC", "path": DRIVES}],
                      folders=[{"name": d, "path": d} for d in drives()])
        if not answer["folders"]:
            answer["message"] = "No drives could be read on this computer."
        return answer

    target = Path(where) if where else Path.home()
    try:
        target = target.resolve()
    except OSError:
        answer.update(path=str(target), label=str(target), readable=False,
                      message="That folder could not be opened.")
        return answer

    answer["path"] = str(target)
    answer["label"] = target.name or str(target)
    answer["breadcrumbs"] = _breadcrumbs(target)

    # Up from a drive root leads to the drive list rather than nowhere.
    if target.parent == target:
        answer["parent"] = DRIVES if on_windows() else None
    else:
        answer["parent"] = str(target.parent)

    if not target.is_dir():
        answer.update(readable=False, message="That is not a folder.")
        return answer

    try:
        entries = sorted(
            (e for e in os.scandir(target) if not e.name.startswith(".")),
            key=lambda e: e.name.lower())
    except OSError:
        answer.update(readable=False,
                      message="This computer will not let the app open that folder.")
        return answer

    folders, loose = [], 0
    for entry in entries:
        try:
            if entry.is_dir():
                folders.append({"name": entry.name, "path": str(Path(entry.path))})
            else:
                loose += 1
        except OSError:
            continue          # one unreadable entry never breaks the list
    answer["folders"] = folders
    # Counted and named as not-jobs, so the screen can say so out loud rather
    # than leaving him to wonder where his documents went.
    answer["loose_files"] = loose
    return answer

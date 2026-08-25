"""What is actually in a job folder, read now, with nothing inferred.

Folder identity is exact. A folder is a direct child directory of the job,
and its identity is that entry's exact name off the disk. This module never
tests a folder name against a path as a string. The scan it replaces did,
with `folder.lower() in str(p.parent).lower()`, so a job living under a
path containing "maps" grew a Maps row it did not have.

Nothing here opens a file. It reads names, sizes and modification dates
from the directory and stops. It never follows a shortcut, so a link
pointing out of the job cannot pull anything in and a link pointing back
into the job cannot loop.
"""
from pathlib import Path
from typing import Optional

import jobs
import workspace
# Taken from jobs rather than from photos, which would make a circle: classify
# reads this module, and photos has to ask classify which files Mark called
# subject photographs. The two helpers do the same thing, and this one also
# treats a path the operating system refuses to resolve as simply not confined,
# so an unreadable file is skipped rather than raised.
from jobs import resolve_confined

# The cap on names sent to one screen. The count always travels separately
# and is always true, the same shape workspace.describe already uses.
FILE_LIMIT = 200

# The app's own thumbnail cache. Already hidden, and named here as well so a
# future cache that is not hidden cannot leak into his file list.
THUMB_DIR = ".rrf-thumbs"


def _skip(name: str) -> bool:
    return name.startswith(".") or name in workspace.NOISE or name == THUMB_DIR


def _entry(path: Path, job: Path, kind: str) -> dict:
    """One file row. `within` is where it sits inside its top-level folder,
    empty when it sits directly in it."""
    parts = path.relative_to(job).parts
    return {"name": path.name,
            "rel": "/".join(parts),
            "within": "/".join(parts[1:-1]),
            "kind": kind}


def _collect(folder: Path, job: Path, out: list) -> None:
    """Every file under this folder, its own subfolders included.

    A shortcut is recognised before anything is opened or walked, listed by
    name, and never followed. That is what stops a link out of the job from
    showing its target's contents, and what stops a link back into the job
    from looping forever.
    """
    for child in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if _skip(child.name):
            continue
        if child.is_symlink():
            out.append(_entry(child, job, "shortcut"))
            continue
        if child.is_dir():
            _collect(child, job, out)
        elif child.is_file() and resolve_confined(child, job) is not None:
            out.append(_entry(child, job, "file"))


def _folder_row(folder: Path, job: Path) -> dict:
    """One folder row, by its exact name on disk.

    A folder that cannot be read says so. Reporting it as empty would be
    stating a fact the app cannot observe, and an empty count is exactly
    what Mark would read as "nothing has arrived".
    """
    row = {"folder": folder.name, "kind": "folder", "count": 0,
           "unreadable": False, "truncated": False, "files": []}
    if folder.is_symlink():
        row["kind"] = "shortcut"
        row["count"] = None
        return row
    found: list = []
    try:
        _collect(folder, job, found)
    except OSError:
        row["unreadable"] = True
        row["count"] = None
        return row
    row["count"] = len(found)
    row["files"] = found[:FILE_LIMIT]
    row["truncated"] = len(found) > FILE_LIMIT
    return row


def read_job(job: Path) -> dict:
    """Every top-level folder actually on disk, plus the loose files.

    Typical folders are the eight Mark's own template carries, in his order.
    Other folders are everything else he has made, by exact name. Nothing is
    hidden for being unrecognised: a folder the app does not understand is
    still a folder he made, and the screen says so.
    """
    typical, other, root_files = [], [], []
    for child in sorted(job.iterdir(), key=lambda p: p.name.lower()):
        if _skip(child.name):
            continue
        if child.is_symlink():
            if child.is_dir():
                other.append(_folder_row(child, job))
            else:
                root_files.append(_entry(child, job, "shortcut"))
        elif child.is_dir():
            (typical if child.name in jobs.MARK_FOLDERS else other).append(
                _folder_row(child, job))
        elif child.is_file() and resolve_confined(child, job) is not None:
            root_files.append(_entry(child, job, "file"))

    order = {name: i for i, name in enumerate(jobs.MARK_FOLDERS)}
    typical.sort(key=lambda r: order[r["folder"]])
    return {"typical": typical, "other": other, "root_files": root_files}


def stat_of(job: Path, rel: str) -> Optional[dict]:
    """Size and modification date of one file, or None when nothing is there.

    The only two facts the app records about a file's contents, and neither
    requires opening it.
    """
    target = job / Path(rel)
    if target.is_symlink() or not target.is_file():
        return None
    if resolve_confined(target, job) is None:
        return None
    info = target.stat()
    return {"size": info.st_size, "mtime": info.st_mtime}


def holds(job: Path, rel: str) -> bool:
    """Whether this exact relative path is a file the inventory would list.

    Every part of the path is checked, not just the last one, so a hidden
    folder, a noise name or the thumbnail cache cannot be classified through
    a hand-written path even though it is a real file on disk.
    """
    parts = Path(rel).parts
    if not parts or any(_skip(part) for part in parts):
        return False
    return stat_of(job, rel) is not None

"""Where Mark's jobs live, and how the app remembers it.

His choice sits in a small JSON file in his home folder. JSON on purpose. A
folder name is arbitrary text off his own disk: it can hold spaces, quotes,
dollar signs, backticks and backslashes. The launcher reads the key file
with the shell, and a path stored that way is executed rather than read.
Measured before this was written: a folder name containing a backtick ran
the command inside it and handed back an empty value. Nothing but Python
reads this file.

Two things this module refuses to do:

- Invent a folder. Not knowing where his jobs are is a real state, and the
  screen says so rather than showing an empty list of an imagined folder.
- Say anything about a folder it has not just looked at. Every count and
  every name in `describe` comes from reading the disk on the spot.
"""
import os
from pathlib import Path
from typing import Optional

import state

SETTINGS_NAME = ".rrf-app.json"
FOLDER_KEY = "jobs_folder"

# Bookkeeping files both operating systems scatter about. Never a job, and
# never worth showing him.
NOISE = {"Thumbs.db", "desktop.ini"}

# A folder can hold hundreds of jobs. The true count always travels; the
# names are capped so one screen cannot be handed a wall of text.
NAME_LIMIT = 100


def settings_file() -> Path:
    """Home folder on both Mac and Windows. RRF_SETTINGS_FILE overrides, for
    tests, the same way RRF_KEY_FILE already does for the key."""
    override = os.environ.get("RRF_SETTINGS_FILE")
    return Path(override) if override else Path.home() / SETTINGS_NAME


def _read() -> dict:
    """The settings, or {} when there is no file at all.

    Raises state.StateUnreadable when the file is there and damaged. That is a
    change from the first version of this module, which returned {} for both
    cases. Returning {} for damage was wrong: it is the same answer as a fresh
    machine, so a truncated file made the app ask him to choose his jobs folder
    again with no explanation and no hint that anything had been lost. The file
    itself is never repaired or guessed at, then or now.
    """
    return state.read_json(settings_file())


def _write(data: dict) -> None:
    """Temporary file then replace, so a failure leaves the previous settings.

    This used to write straight over the real file. His chosen jobs folder and
    his active job list both live in here, so a half-written save lost both at
    once.
    """
    state.write_json(settings_file(), state.without_schema(data))


def saved_folder() -> str:
    value = _read().get(FOLDER_KEY, "")
    return value if isinstance(value, str) else ""


def save_folder(path: str) -> None:
    """Remember this folder. Every other line in the file is left alone."""
    data = _read()
    data[FOLDER_KEY] = str(path)
    _write(data)


def forget_folder() -> None:
    """Forget which folder his jobs are in, and nothing else.

    Only this one key goes. Every other setting in the file survives, and
    the key file next door is never opened. Nothing on disk is touched, so
    choosing the same folder again puts everything back exactly as it was.
    """
    data = _read()
    data.pop(FOLDER_KEY, None)
    _write(data)


def active_jobs(parent: Path) -> list:
    """The folder names Mark has marked active under this parent folder.

    Keyed by the resolved parent, so two parent folders keep their own
    answers. A name and nothing else: no status, no nickname, no parsing.
    """
    entry = _read().get("workspaces", {}).get(str(Path(parent).resolve()), {})
    names = entry.get("active", []) if isinstance(entry, dict) else []
    return [n for n in names if isinstance(n, str)]


def save_active_jobs(parent: Path, names: list) -> None:
    data = _read()
    spaces = data.setdefault("workspaces", {})
    if not isinstance(spaces, dict):
        spaces = {}
        data["workspaces"] = spaces
    spaces[str(Path(parent).resolve())] = {
        "active": sorted({str(n) for n in names if str(n).strip()})
    }
    _write(data)


def forget_demo_state(parent: Optional[Path]) -> None:
    """What the demo reset clears: the chosen folder and this parent's active
    list, and nothing else. If that empties the file, the file goes too, so a
    reset leaves no leftovers behind for the next run to inherit."""
    data = _read()
    data.pop(FOLDER_KEY, None)
    spaces = data.get("workspaces")
    if isinstance(spaces, dict):
        if parent is not None:
            spaces.pop(str(Path(parent).resolve()), None)
        if not spaces:
            data.pop("workspaces", None)
    if state.without_schema(data):
        _write(data)
    else:
        path = settings_file()
        if path.is_file():
            path.unlink()


def jobs_home() -> Optional[Path]:
    """The folder his jobs live in, or None when he has not chosen one.

    RRF_JOBS_HOME stays the override for tests and development. Below that,
    his saved choice. Below that, nothing: there is no invented default.
    """
    override = os.environ.get("RRF_JOBS_HOME")
    if override:
        return Path(override)
    saved = saved_folder()
    return Path(saved) if saved else None


def suggested_start() -> str:
    """Where to open the picker. His current folder if it is still there,
    otherwise his home folder, which exists on both machines."""
    home = jobs_home()
    if home is not None and home.is_dir():
        return str(home)
    return str(Path.home())


def child_folder_names(path: Path) -> list:
    """Every immediate child folder, by exact name, uncapped.

    describe() below caps its list, because that one feeds a preview of a
    folder he has not committed to yet. This one feeds the screen where he
    picks his active jobs, and that screen has to show all of them.
    """
    names = []
    for entry in path.iterdir():
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            names.append(entry.name)
    names.sort()
    return names


def describe(path: Path) -> dict:
    """What is actually in this folder, read now.

    Only immediate children count. A folder directly inside is a candidate
    job; a loose file sitting beside them is not, and is counted separately
    so the screen can say so out loud. Hidden entries are skipped, the same
    way the jobs list already skips them, because none of his jobs is
    hidden.
    """
    facts = {"path": str(path), "exists": False, "is_folder": False,
             "readable": False, "folder_count": 0, "folder_names": [],
             "folder_names_truncated": False, "loose_file_count": 0}

    if not path.exists():
        return facts
    facts["exists"] = True
    if not path.is_dir():
        return facts
    facts["is_folder"] = True

    names, loose = [], 0
    try:
        for entry in path.iterdir():
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                names.append(entry.name)
            elif entry.name not in NOISE:
                loose += 1
    except OSError:
        # There, but shut. Saying "no folders" here would be a lie.
        return facts

    facts["readable"] = True
    names.sort()
    facts["folder_count"] = len(names)
    facts["folder_names"] = names[:NAME_LIMIT]
    facts["folder_names_truncated"] = len(names) > NAME_LIMIT
    facts["loose_file_count"] = loose
    return facts


def status() -> dict:
    """What the screens are allowed to know about the current choice."""
    home = jobs_home()
    if os.environ.get("RRF_JOBS_HOME"):
        source = "override"
    elif saved_folder():
        source = "saved"
    else:
        source = "none"

    if home is None:
        return {"chosen": False, "valid": False, "source": source,
                "path": "", "exists": False, "is_folder": False,
                "readable": False, "folder_count": 0, "folder_names": [],
                "folder_names_truncated": False, "loose_file_count": 0}

    facts = describe(home)
    # Chosen and valid are different questions. A folder he picked last month
    # and has since moved is still chosen, and the screen has to say what
    # became of it rather than pretend he never picked anything.
    return {"chosen": True,
            "valid": facts["exists"] and facts["is_folder"] and facts["readable"],
            "source": source, **facts}

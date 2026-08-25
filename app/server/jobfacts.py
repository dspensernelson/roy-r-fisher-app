"""Mark's corrections to what the app read out of a brief, stored app-side.

The city and the street address are recovered from `job-brief.md`, which holds
them as one joined string. Recovering two values from one string is parsing,
and parsing can be wrong: a street with a comma in it, a unit number, a brief
written by hand or by the older onboarding skill can all split differently
from the way the app wrote them.

So the parse is shown to him before it is used, and if it is wrong he corrects
it. The correction lives here, in the app's own file in his home folder, and
never in one of his job folders. That is the same rule the classification store
already follows.

The same file also holds which folder inside `Photos` holds the report
photographs, because that is another answer only Mark can give. His office
keeps every shoot twice, full size and hand-shrunk, under a folder name that
varies from job to job, so the app asks him once rather than guessing.
"""
import os
from pathlib import Path

import state

STORE_NAME = ".rrf-job-facts.json"

CITY = "city"
ADDRESS = "address"
PHOTO_FOLDER = "photo_folder"


def store_file() -> Path:
    """Home folder on both Mac and Windows. RRF_JOBFACTS_FILE overrides, for
    tests, the same way RRF_KEY_FILE already does for the key."""
    override = os.environ.get("RRF_JOBFACTS_FILE")
    return Path(override) if override else Path.home() / STORE_NAME


def _key(job: Path) -> str:
    return str(Path(job).resolve())


def _entry(job: Path) -> dict:
    """Everything recorded about this job, whatever the keys are.

    Deliberately unfiltered. `for_job` below narrows to the two naming fields
    for its own callers, and a filter here as well would hide the folder
    choice from the code that stores it.
    """
    entry = state.read_json(store_file()).get("jobs", {}).get(_key(job), {})
    return entry if isinstance(entry, dict) else {}


def _save_entry(job: Path, entry: dict) -> None:
    """Write one job's answers back, leaving every other job alone.

    An empty entry removes the job rather than leaving a hollow record, so a
    job he has answered nothing about takes up no space and reads the same as
    one he has never opened.
    """
    data = state.read_json(store_file())
    everything = data.setdefault("jobs", {})
    if not isinstance(everything, dict):
        everything = {}
        data["jobs"] = everything
    if entry:
        everything[_key(job)] = entry
    else:
        everything.pop(_key(job), None)
    state.write_json(store_file(), state.without_schema(data))


def for_job(job: Path) -> dict:
    """The city and address corrections only. The folder choice has its own
    reader below, because its callers and its meaning are different."""
    return {k: v for k, v in _entry(job).items() if k in (CITY, ADDRESS)
            and isinstance(v, str)}


def save(job: Path, city: str, address: str) -> dict:
    """Record his answer. Blank means "no correction", not "blank value".

    Merges over what is already recorded rather than replacing it. This used
    to write a fresh entry holding only the city and the address, which threw
    away any other answer he had given about the same job. With the folder
    choice living here too, that would have meant correcting an address a week
    later silently changed which photographs went into his report, with
    nothing on screen to say so.
    """
    entry = _entry(job)
    for key, value in ((CITY, city), (ADDRESS, address)):
        if str(value).strip():
            entry[key] = str(value).strip()
        else:
            entry.pop(key, None)
    _save_entry(job, entry)
    return {k: v for k, v in entry.items() if k in (CITY, ADDRESS)}


def photo_folder(job: Path):
    """Which folder inside `Photos` holds the report photographs.

    A POSIX path relative to `Photos`, or "" when he chose the top of `Photos`
    itself, or None when he has not been asked or has not answered.

    "" and None are different answers. "" is a decision and the app acts on
    it; None means the app still has no idea and may need to ask. Collapsing
    them would make a job he answered look unanswered every time.
    """
    found = _entry(job).get(PHOTO_FOLDER)
    return found if isinstance(found, str) else None


def save_photo_folder(job: Path, folder: str) -> None:
    """Record which folder he picked, and change nothing else about the job."""
    entry = _entry(job)
    entry[PHOTO_FOLDER] = str(folder)
    _save_entry(job, entry)


def forget_photo_folder(job: Path) -> None:
    """Put the job back to never having been asked. His naming corrections
    stay exactly as they were."""
    entry = _entry(job)
    entry.pop(PHOTO_FOLDER, None)
    _save_entry(job, entry)

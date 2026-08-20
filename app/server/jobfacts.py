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
"""
import os
from pathlib import Path

import state

STORE_NAME = ".rrf-job-facts.json"

CITY = "city"
ADDRESS = "address"


def store_file() -> Path:
    """Home folder on both Mac and Windows. RRF_JOBFACTS_FILE overrides, for
    tests, the same way RRF_KEY_FILE already does for the key."""
    override = os.environ.get("RRF_JOBFACTS_FILE")
    return Path(override) if override else Path.home() / STORE_NAME


def _key(job: Path) -> str:
    return str(Path(job).resolve())


def for_job(job: Path) -> dict:
    entry = state.read_json(store_file()).get("jobs", {}).get(_key(job), {})
    if not isinstance(entry, dict):
        return {}
    return {k: v for k, v in entry.items() if k in (CITY, ADDRESS)
            and isinstance(v, str)}


def save(job: Path, city: str, address: str) -> dict:
    """Record his answer. Blank means "no correction", not "blank value"."""
    data = state.read_json(store_file())
    everything = data.setdefault("jobs", {})
    if not isinstance(everything, dict):
        everything = {}
        data["jobs"] = everything

    entry = {}
    if str(city).strip():
        entry[CITY] = str(city).strip()
    if str(address).strip():
        entry[ADDRESS] = str(address).strip()

    if entry:
        everything[_key(job)] = entry
    else:
        everything.pop(_key(job), None)
    state.write_json(store_file(), state.without_schema(data))
    return entry

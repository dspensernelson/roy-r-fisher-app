"""What the appraiser has confirmed a file is, stored outside his folders.

A classification is something the app knows, not something in his job. The
Never list says app knowledge never goes into one of his folders, so it
lives in the app's own file in his home folder, the same way the key file
and the workspace settings already do. `photo-manifest.json` sits inside a
job and stays a narrow existing exception; this does not widen it.

Nothing here opens a file. Recording a classification reads the file's size
and modification date from the directory, which is all the app needs to
notice later that something else now has that name.

A label is only ever chosen by the appraiser from the approved list. Nothing in this
module reads a filename to guess one, and nothing may add to the list.
"""
import datetime
import json
import os
from pathlib import Path
from typing import Optional

import inventory

STORE_NAME = ".rrf-classifications.json"

# Approved by Spenser on 2026-08-16. Exactly these nine, no free text.
# Building sketch and Flood map were considered and deliberately left out of
# this first slice. Adding to this list is a product decision, not a code one.
LABELS = (
    "Engagement letter",
    "Deed",
    "Assessor or tax record",
    "Subject photograph",
    "Plat map",
    "Neighborhood map",
    "Aerial photo",
    "Comparable sale document",
    "Valuation workbook",
)


def store_file() -> Path:
    """Home folder on both Mac and Windows. RRF_CLASSIFY_FILE overrides, for
    tests, the same way RRF_KEY_FILE already does for the key."""
    override = os.environ.get("RRF_CLASSIFY_FILE")
    return Path(override) if override else Path.home() / STORE_NAME


def _read() -> dict:
    path = store_file()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeDecodeError):
        # A store we cannot read counts as no answers at all. It is never
        # repaired or guessed at: a guessed classification is exactly the
        # confident wrong answer this app must not produce.
        return {}
    return data if isinstance(data, dict) else {}


def _write(data: dict) -> None:
    """Write through a temporary file in the same folder, then replace.

    A half-written store would lose every answer the appraiser has given. Writing
    beside the real file and swapping means a failure leaves the previous
    file exactly as it was.
    """
    path = store_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".writing")
    try:
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        os.replace(str(temp), str(path))
    finally:
        if temp.exists():
            temp.unlink()


def _key(job: Path) -> str:
    """One job, by its resolved path. Same keying workspace already uses for
    the parent folder, so two folders of the same name stay separate."""
    return str(Path(job).resolve())


def for_job(job: Path) -> dict:
    entry = _read().get("jobs", {}).get(_key(job), {})
    if not isinstance(entry, dict):
        return {}
    return {rel: rec for rel, rec in entry.items() if isinstance(rec, dict)}


def set_label(job: Path, rel: str, label: str) -> dict:
    """Record the appraiser's answer for one file. Confirmed, never a suggestion.

    Raises ValueError for a label outside the approved list and LookupError
    when nothing the inventory would list sits at that path, so a record can
    never exist for a file the app has not just observed.
    """
    if label not in LABELS:
        raise ValueError("that is not one of the classifications")
    if not inventory.holds(job, rel):
        raise LookupError(rel)
    facts = inventory.stat_of(job, rel)
    record = {"label": label,
              "confirmed_at": datetime.date.today().isoformat(),
              "size": facts["size"],
              "mtime": facts["mtime"]}

    data = _read()
    everything = data.setdefault("jobs", {})
    if not isinstance(everything, dict):
        everything = {}
        data["jobs"] = everything
    mine = everything.setdefault(_key(job), {})
    if not isinstance(mine, dict):
        mine = {}
        everything[_key(job)] = mine
    mine[rel] = record
    _write(data)
    return record


def remove_label(job: Path, rel: str) -> None:
    """Forget the app's own note about this file, and nothing else.

    Works whether or not the file is still there, which is how the appraiser clears a
    record whose file he has since renamed. Nothing in his folders is
    touched: the file, if it exists, is left exactly as it is.
    """
    data = _read()
    everything = data.get("jobs")
    if not isinstance(everything, dict):
        return
    mine = everything.get(_key(job))
    if not isinstance(mine, dict):
        return
    mine.pop(rel, None)
    if not mine:
        everything.pop(_key(job), None)
    _write(data)


def state_of(job: Path, rel: str, record: Optional[dict] = None) -> str:
    """present, changed, or missing. Nothing else, and never a guess.

    changed means something with that name is there but it is not the file
    the appraiser confirmed. The app cannot tell what it is now, so it says only that
    it is different and stops presenting the old answer as current.
    """
    if record is None:
        record = for_job(job).get(rel)
    if not record:
        return "missing"
    facts = inventory.stat_of(job, rel)
    if facts is None:
        return "missing"
    same = (facts["size"] == record.get("size")
            and facts["mtime"] == record.get("mtime"))
    return "present" if same else "changed"

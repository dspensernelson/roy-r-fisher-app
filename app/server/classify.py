"""What Mark has confirmed a file is, stored outside his folders.

A classification is something the app knows, not something in his job. The
Never list says app knowledge never goes into one of his folders, so it
lives in the app's own file in his home folder, the same way the key file
and the workspace settings already do. `photo-manifest.json` sits inside a
job and stays a narrow existing exception; this does not widen it.

Nothing here opens a file. Recording a classification reads the file's size
and modification date from the directory, which is all the app needs to
notice later that something else now has that name.

A label is only ever chosen by Mark from the approved list. Nothing in this
module reads a filename to guess one, and nothing may add to the list.
"""
import datetime
import os
from pathlib import Path
from typing import Optional

import inventory
import state

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
    """Mark's answers, or {} when there is no store at all.

    Raises state.StateUnreadable when the store is there and damaged. This
    used to return {} for damage as well, which quietly presented every
    classification he had given as never given. A guessed classification is
    the confident wrong answer this app must not produce, and so is a silently
    forgotten one. The damaged file is never repaired or guessed at.
    """
    return state.read_json(store_file())


def _write(data: dict) -> None:
    """Temporary file in the same folder, then replace.

    This module already worked this way and the behaviour is unchanged. It now
    shares one helper with the other app-owned files instead of keeping its own
    copy, so the safe path is the only path any of them can take.
    """
    state.write_json(store_file(), state.without_schema(data))


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
    """Record Mark's answer for one file. Confirmed, never a suggestion.

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

    Works whether or not the file is still there, which is how Mark clears a
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


def attach(job: Path, listing: dict) -> dict:
    """Put Mark's answers beside the files, and never lose one.

    A record whose file has gone still comes back: inside its folder while
    that folder is still there, and in missing_classifications once it is
    not. An answer he gave is his. The app does not quietly forget it
    because something moved, and it does not go on claiming the file is
    there either.

    A missing file is never counted. The count on a folder row stays what
    the app actually observed in it.
    """
    records = for_job(job)
    placed = set()

    def decorate(entry: dict) -> None:
        record = records.get(entry["rel"])
        if record is None:
            entry["classification"] = None
            return
        entry["classification"] = {"label": record["label"],
                                   "state": state_of(job, entry["rel"], record)}
        placed.add(entry["rel"])

    rows = listing["typical"] + listing["other"]
    for row in rows:
        for entry in row["files"]:
            decorate(entry)
    for entry in listing["root_files"]:
        decorate(entry)

    by_folder = {row["folder"]: row for row in rows}
    homeless = []
    for rel in sorted(records):
        # Past the display cap is not the same as gone, so ask the disk.
        if rel in placed or inventory.holds(job, rel):
            continue
        parts = rel.split("/")
        entry = {"name": parts[-1], "rel": rel,
                 "within": "/".join(parts[1:-1]), "kind": "missing",
                 "classification": {"label": records[rel]["label"],
                                    "state": "missing"}}
        if len(parts) == 1:
            listing["root_files"].append(entry)
        elif parts[0] in by_folder:
            by_folder[parts[0]]["files"].append(entry)
        else:
            homeless.append(entry)

    listing["missing_classifications"] = homeless
    return listing


def state_of(job: Path, rel: str, record: Optional[dict] = None) -> str:
    """present, changed, or missing. Nothing else, and never a guess.

    changed means something with that name is there but it is not the file
    Mark confirmed. The app cannot tell what it is now, so it says only that
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

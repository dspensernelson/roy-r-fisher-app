"""Turn the engine's readiness result into the rows the job screen draws.

The engine (app/engine/readiness_scan.py) owns WHAT a job needs.
This module only decides how those needs group onto Mark's folders, so the
requirement patterns never get restated here.
"""
import sys
from pathlib import Path

import jobs

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from readiness_scan import scan_job  # noqa: E402

# The engine's requirement table carries no filename patterns for Photos or
# Comps, because it counts those two separately rather than pattern-matching
# them. Left at that, both rows would report "nothing missing" while sitting
# empty. They are the two folders Mark fills first, so those counts get
# turned back into a plain here-or-needed line.
COUNTED = {
    "Photos": ("photos", lambda result: result["photos"]["usable"]),
    "Comps": ("comparable sales", lambda result: result["comps"]["count"]),
}


def _count_files(folder: Path) -> int:
    if not folder.is_dir():
        return 0
    return sum(1 for p in folder.iterdir()
               if p.is_file() and p.name not in (".DS_Store", "Thumbs.db", "desktop.ini"))


def folder_rows(job: Path) -> list:
    """One row per folder Mark has, saying what is here and what is missing."""
    result = scan_job(job)
    rows = {name: {"folder": name, "count": _count_files(job / name), "here": [], "needs": []}
            for name in jobs.MARK_FOLDERS}

    for checks in result["sections"].values():
        for check in checks:
            for folder in check["folder"].split("|"):
                row = rows.get(folder)
                if row is None:
                    continue        # a folder that only exists later, e.g. Improvements
                bucket = "here" if check["hits"] else "needs"
                if check["note"] not in row[bucket]:
                    row[bucket].append(check["note"])

    for folder, (label, count_of) in COUNTED.items():
        row = rows.get(folder)
        if row is None:
            continue
        row["here" if count_of(result) else "needs"].append(label)

    for row in rows.values():
        row["status"] = "waiting" if row["needs"] else "ready"
    return [rows[name] for name in jobs.MARK_FOLDERS]

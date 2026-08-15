#!/usr/bin/env python3
"""Readiness scan: compare a job folder's contents against required-input patterns.

Usage: python3 readiness_scan.py "/path/to/job folder"

Prints a per-section readiness report the conductor pastes into checklist.md.
Patterns mirror the GUIDE.md required-inputs tables. Case-insensitive substring/glob matching,
deliberately loose: a MISSING verdict means "nothing plausible found", not certainty.
The conductor (or Mark) confirms borderline matches.
"""
import sys, re
from pathlib import Path

# (section, folder, [patterns], requirement note). Patterns are lowercase substrings; any match = present.
REQUIREMENTS = [
    ("Intake docs", "Subject Information", ["engagement", "signed proposal"], "engagement letter/proposal"),
    ("Intake docs", "Subject Information", ["deed"], "deed"),
    ("Intake docs", "Subject Information", ["assessment", "property tax", "tax.", "beacon", "parcel report"], "assessment/tax record"),
    ("Improvements", "Subject Information|Improvements", ["prc"], "assessor PRC"),
    ("Improvements", "Improvements", ["improvement template", "improvement"], "improvement template"),
    ("Improvements", "Transcript information", ["transcript"], "inspection transcript"),
    ("Neighborhood", "Transcript information", ["neighborhood"], "neighborhood transcript/dictation"),
    ("Neighborhood", "Maps", ["neighborhood"], "neighborhood map"),
    ("Neighborhood", "Maps", ["traffic"], "traffic map with counts"),
    ("Site Analysis", "Maps", ["plat"], "plat map"),
    ("Site Analysis", "Maps", ["flood", "riskmeter"], "flood map"),
    ("Site Analysis", "Maps", ["zoning"], "zoning snip/legend/description"),
    ("Improvements exhibit", "Maps", ["sketch"], "building sketch"),
    ("Market Overview", "Demographic", ["market_profile", "market profile"], "ESRI market profile"),
    ("Market Overview", "Demographic", ["submarket"], "CoStar submarket report"),
    ("Market Overview", "Demographic|Maps", ["site_map", "site map"], "ESRI site map"),
    ("Photos", "Photos", [], "captioned photo copies (checked separately below)"),
    ("Income Approach", "Financials", ["financial", "profit and loss", "rent roll", "rent and cam", " is."], "owner history / rent roll"),
    ("Sales Comparison", "Comps", [], "comp documents (counted below)"),
]

EXCLUDE = ("old report", "drafts", "do not use")


def _index(job: Path):
    """Every file in the job that could satisfy an input.

    Old Report and Drafts are excluded: prior-job and working files never
    satisfy a current-job input.
    """
    return [p for p in job.rglob("*")
            if p.is_file() and p.name not in (".DS_Store", "Thumbs.db", "desktop.ini")
            and ".rrf-thumbs" not in p.parts
            and not any(x in str(p.parent).lower() for x in EXCLUDE)]


def scan_job(job) -> dict:
    """The readiness result as data, for callers that render it themselves.

    main() prints from this, and the app draws its folder rows from it, so
    the requirement patterns above stay the single source of truth for what
    a job needs.
    """
    job = Path(job)
    files = _index(job)

    def in_folder(p, folders):
        return any(f.lower() in str(p.parent).lower() for f in folders.split("|"))

    sections: dict = {}
    for section, folder, pats, note in REQUIREMENTS:
        if not pats:
            continue
        hits = [p for p in files if in_folder(p, folder) and any(x in p.name.lower() for x in pats)]
        sections.setdefault(section, []).append({
            "note": note, "folder": folder,
            "hits": [p.relative_to(job).as_posix() for p in hits],
        })

    # captioned copies = jpg/jpeg outside Original|Do Not Use whose stem has a non-numeric suffix
    photos = [p for p in files if p.suffix.lower() in (".jpg", ".jpeg", ".png")
              and "photos" in str(p.parent).lower()
              and "original" not in str(p.parent).lower()
              and "do not use" not in str(p.parent).lower()]
    captioned = [p for p in photos
                 if re.search(r"[a-zA-Z]{3,}", p.stem.replace("IMG", "").replace("ANMP", ""))]
    comps = [p for p in files if "comps" in str(p.parent).lower() and p.suffix.lower() == ".pdf"]
    xlsm = list(job.glob("*.xlsm"))

    return {
        "sections": sections,
        "photos": {"usable": len(photos), "captioned": len(captioned)},
        "comps": {"count": len(comps)},
        "workbook": xlsm[0].name if xlsm else None,
        "brief": (job / "job-brief.md").exists(),
    }


def main(job):
    job = Path(job)
    if not job.is_dir():
        sys.exit(f"Not a folder: {job}")
    result = scan_job(job)
    print(f"READINESS SCAN - {job.name}\n" + "=" * 60)

    for section, checks in result["sections"].items():
        missing = [c["note"] for c in checks if not c["hits"]]
        status = "READY (inputs present)" if not missing else f"BLOCKED - missing: {', '.join(missing)}"
        print(f"\n[{section}] {status}")
        for check in checks:
            mark = "+" if check["hits"] else "-"
            example = f"  e.g. {check['hits'][0]}" if check["hits"] else ""
            print(f"  {mark} {check['note']}{example}")

    photos, captioned = result["photos"]["usable"], result["photos"]["captioned"]
    print(f"\n[Photos] {photos} usable photos, {captioned} appear captioned "
          f"({'READY' if captioned >= 5 else 'BLOCKED - need captioned copies or a caption pass'})")
    comps = result["comps"]["count"]
    print(f"[Comps] {comps} comp documents found "
          f"({'plausible' if comps >= 3 else 'thin - check with Mark'})")
    print(f"[Job xlsm] {'found: ' + result['workbook'] if result['workbook'] else 'MISSING - numbers contract unavailable'}")
    print(f"[job-brief.md] {'present' if result['brief'] else 'MISSING - run intake first'}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")

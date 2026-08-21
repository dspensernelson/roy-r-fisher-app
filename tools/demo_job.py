"""The practice jobs that ship inside the Windows package.

Mark's package needs something to open. Without it the first thing he sees
after launching is a folder picker pointing at nothing, and the Subject
Photographs workflow cannot be tried at all.

Two jobs ship, and they exist to exercise two different paths:

- twelve photographs, the ordinary run, below the confirmation threshold
- sixty-one photographs, which needs the spend confirmation and divides
  itself into two tranches of 60 + 1

Both hold real property photographs, sanitised copies made through
`photo_source`: rebuilt from the pixels so no EXIF or GPS survives, generically
named so no client filename or date travels, and carrying no document, address,
caption or report content. Earlier versions of this shipped flat coloured
panels, which were useless for judging a layout, a caption, or a document size.

The jobs themselves are invented. The addresses, the client and the brief are
made up, so nothing in a practice job points at a real property even though the
photographs inside it are real ones with their identifying information removed.

If the approved photograph source is not on the build machine this raises
rather than substituting anything. A practice job full of placeholders is what
this replaced, and shipping one silently would be worse than failing the build.

One thing is deliberately left out. Neither job carries a HEIC, because the
packaged interpreter's HEIC support is unproven on Windows until Gate D and a
practice job with a button that fails is not a practice job.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import photo_source

DEMO_PARENT = "Demo Jobs"

# Obviously invented. A real city and a real street would be the one thing
# somebody might later mistake for a client's job.
ORDINARY = {
    "name": "ANYTOWN_100 Example Avenue - 2026",
    "street": "100 Example Avenue",
    "city": "Anytown",
    "photos": 12,
    "note": "the ordinary run, below the confirmation threshold",
}
LARGE = {
    "name": "ANYTOWN_200 Example Avenue - 61 Photo Test",
    "street": "200 Example Avenue",
    "city": "Anytown",
    "photos": 61,
    "note": "needs the spend confirmation, and divides into 60 + 1",
}
JOBS = (ORDINARY, LARGE)

STATE = "Iowa"

# Kept for the older name some tests and notes still use.
JOB_NAME = ORDINARY["name"]


def build_job(home: Path, spec: dict, pool: list, offset: int) -> Path:
    """One practice job: Mark's folders, a fictional brief, real photographs."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app" / "server"))
    import brief
    import jobs as jobs_module

    job = home / spec["name"]
    for folder in jobs_module.MARK_FOLDERS:
        (job / folder).mkdir(parents=True, exist_ok=True)

    # Written by the app's own writer rather than by hand, so the brief cannot
    # drift from the shape the app reads back.
    brief.write_brief(job, {
        "Property address": "%s, %s, %s" % (spec["street"], spec["city"], STATE),
        "Property type": "Retail",
        "Engagement type": "Full appraisal",
        "Client (intended user)": "Example Bank (fictional)",
        "Intended use": "Practice dataset for testing this app",
        "Effective date of value": "2026-01-01",
        "Report due date": "2026-02-01",
        "Office file number": "DEMO-%04d" % spec["photos"],
    }, sections=[])

    photos_dir = job / "Photos"
    photos_dir.mkdir(parents=True, exist_ok=True)
    for i in range(spec["photos"]):
        source = pool[(offset + i) % len(pool)]
        photo_source.sanitise(source, photos_dir / ("photo-%02d.jpg" % (i + 1)))
    return job


def build(parent: Path) -> Path:
    """Create `<parent>/Demo Jobs/` with both practice jobs in it.

    Returns the ordinary job, which is what earlier callers expected.
    """
    home = Path(parent) / DEMO_PARENT
    home.mkdir(parents=True, exist_ok=True)

    needed = sum(spec["photos"] for spec in JOBS)
    pool = photo_source.require(needed)

    made, offset = [], 0
    for spec in JOBS:
        made.append(build_job(home, spec, pool, offset))
        offset += spec["photos"]

    (home / "READ ME.txt").write_text(
        "Practice material\n"
        "=================\n"
        "\n"
        "Two jobs to try the app on. The jobs, the addresses and the client are\n"
        "all invented. The photographs are real building photographs with their\n"
        "camera information removed, so there is no location, no date and no\n"
        "file name from anybody's job in any of them.\n"
        "\n"
        "  %s\n"
        "      %d photos. The ordinary run.\n"
        "\n"
        "  %s\n"
        "      %d photos. Enough that the app asks you to confirm the cost\n"
        "      first, and enough that it writes them in two goes.\n"
        "\n"
        "Point the app at this Demo Jobs folder, open a job, and use its Photos\n"
        "folder to build a Subject Photographs document.\n"
        "\n"
        "Nothing here is sent anywhere unless you press Generate captions.\n"
        % (ORDINARY["name"], ORDINARY["photos"], LARGE["name"], LARGE["photos"]),
        encoding="utf-8")
    return made[0]


if __name__ == "__main__":
    where = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    build(where)
    for spec in JOBS:
        print("built %s (%d photos): %s" % (spec["name"], spec["photos"], spec["note"]))

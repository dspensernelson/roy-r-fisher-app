import re
import shutil
from pathlib import Path
from typing import Optional

import brief
import thumbcache
import workspace

PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".heic"}

# Folders inside Photos that are never walked for photographs. The legacy
# thumbnail cache is the app's own, and it is skipped rather than listed so a
# Photos folder from before thumbnails moved out still reads correctly.
PHOTO_SKIP_DIRS = {thumbcache.LEGACY_THUMB_DIR}
SAFE_NAME = re.compile(r"^[^/\\]{1,120}$")

# Mark's own eight folders, in the order his folder template carries them.
# The job screen draws one row per entry, so this is the list that decides
# what "the folders" means anywhere in the app. Folders the engine needs
# later (Old Report, Output, Legal, Improvements, Transcript information)
# are not here on purpose: they appear only when a module actually needs
# one, so nothing unexplained ever shows up in a job.
MARK_FOLDERS = [
    "# and Date",
    "Comps",
    "Demographic",
    "Drafts",
    "Financials",
    "Maps",
    "Photos",
    "Subject Information",
]


def jobs_home() -> Optional[Path]:
    """The folder his jobs live in, or None when he has not chosen one yet.

    Mark chooses this on a screen now, and workspace.py owns the answer.
    There used to be a made-up fallback here, Documents/RRF Jobs, which the
    app reported as though it were real whether or not it existed.
    """
    return workspace.jobs_home()


# Measured from the nine corpus folder names: CITY_Address is constant and
# the suffix varies by engagement shape.
NAME_SUFFIX = {
    "Tax appeal": " - {year} Tax",
    "Rent study": " - Rent Study",
    "Right of way": " ROW",
    "Full appraisal": " - {year}",
    "Restricted short form": " - {year}",
}

# Windows refuses these in a filename. Stripping them here means a name the
# app proposes can always actually be created on Mark's machine.
WINDOWS_FORBIDDEN = '<>:"/\\|?*'


def propose_folder_name(city: str, street: str, engagement: str, year: int) -> str:
    """A folder name in the firm's house style, for Mark to accept or edit."""
    base = f"{city.strip().upper()}_{street.strip()}".strip("_ ")
    suffix = NAME_SUFFIX.get(engagement, " - {year}").format(year=year)
    name = "".join(ch for ch in (base + suffix) if ch not in WINDOWS_FORBIDDEN and ch >= " ")
    name = re.sub(r"\s+", " ", name).strip().lstrip("-").strip()
    return (name[:120].strip().rstrip(". ") or f"New job {year}")


def photos_dir(job: Path) -> Path:
    return job / "Photos"


def resolve_confined(path: Path, base: Path):
    """`path` resolved, or None if the real thing on disk sits outside `base`.

    Resolving follows symlinks, so this catches a name that is harmless as a
    string but points somewhere else on disk. Lives here rather than in
    photos.py because the photo walk below needs it and photos.py already
    imports this module.
    """
    try:
        resolved = path.resolve()
        resolved.relative_to(base.resolve())
    except (OSError, ValueError):
        return None
    return resolved


def _walk_photos(root: Path):
    """One pass over the Photos tree, answering both questions about it.

    Returns (photographs, every_name). The first is the photos to show, the
    second is the bare name of every entry of any kind anywhere in the tree,
    which is what tells an existing manifest entry apart from a deleted one.

    Measured against the nine real jobs in the corpus on 2026-08-24: four of
    them keep no photographs directly in Photos at all. Mason City's are in
    `Raw pics_Walmart...`, Brookside's are split across `3525` and `3575`,
    Elmore Circle's are in `full size` and `Building`. Reading only the top of
    Photos, which is what this did until now, showed Mark an empty screen on
    those four jobs with nothing on it to say why.

    A subfolder is often a second copy at another size rather than more
    photographs: Bettendorf's `Original` holds the same 71 filenames as the top
    of Photos, and 4300 E 53rd's `Minimized` holds 11 of its 12. So a filename
    already seen is passed over, and the top of Photos is read first, which
    makes the copy Mark works from the one that wins. Names are compared
    case-folded because Windows would treat IMG_1.JPG and img_1.jpg as one file
    anyway.

    Symlink loops are bounded by remembering resolved folders rather than by
    capping the depth: a depth cap would silently stop listing photographs in a
    tree that was merely nested, which is the failure this whole function
    exists to end.
    """
    photographs: list = []
    every_name: set = set()
    seen: set = set()
    visited: set = set()

    def walk(folder: Path) -> None:
        resolved = resolve_confined(folder, root)
        if resolved is None or resolved in visited:
            return
        visited.add(resolved)
        try:
            entries = sorted(folder.iterdir(), key=lambda e: e.name.lower())
        except OSError:
            # An unreadable folder is one Mark cannot use either. The photos
            # that were readable still list, rather than the whole job failing.
            return
        subfolders = []
        for entry in entries:
            every_name.add(entry.name)
            if entry.is_dir():
                if entry.name not in PHOTO_SKIP_DIRS and not entry.name.startswith("."):
                    subfolders.append(entry)
                continue
            if entry.suffix.lower() not in PHOTO_EXTS:
                continue
            key = entry.name.lower()
            if key in seen or resolve_confined(entry, root) is None:
                continue
            seen.add(key)
            photographs.append(entry)
        # Files at this level before anything nested under it, so the loose
        # copy of a photograph outranks the one in Original or Minimized.
        for sub in subfolders:
            walk(sub)

    walk(root)
    return photographs, every_name


def photo_files(job: Path) -> list:
    """Every photograph in the job, wherever inside Photos it sits."""
    root = photos_dir(job)
    return _walk_photos(root)[0] if root.is_dir() else []


def photo_names(job: Path) -> set:
    """Bare name of every entry anywhere in the Photos tree, any type."""
    root = photos_dir(job)
    return _walk_photos(root)[1] if root.is_dir() else set()


def photo_folder(job: Path, photo: Path) -> str:
    """Which subfolder of Photos a photograph came from, POSIX, '' for the top.

    Stored on the manifest entry beside the bare filename rather than folded
    into it. The filename stays the photo's identity everywhere -- the manifest
    key, the caption lookup, the thumbnail URL -- so a manifest written before
    subfolders were read still loads with no migration and means exactly what
    it always meant.
    """
    try:
        rel = photo.parent.relative_to(photos_dir(job))
    except ValueError:
        return ""
    return "" if str(rel) == "." else rel.as_posix()


def photo_path(job: Path, entry: dict) -> Path:
    """Where one manifest entry's photograph actually sits on disk.

    The one place that turns an entry back into a path, so the screen, the
    thumbnail and the built document can never disagree about it.
    """
    root = photos_dir(job)
    folder = str(entry.get("folder") or "")
    return root.joinpath(*folder.split("/"), entry.get("file", "")) if folder \
        else root / entry.get("file", "")


def count_photos(job: Path) -> int:
    return len(photo_files(job))


def resolve_job(home: Optional[Path], name: str) -> Path:
    # No folder chosen yet means no job can resolve. Same refusal as a bad
    # name, so no caller has to learn a second failure shape.
    if home is None:
        raise ValueError("no jobs folder chosen")
    if not SAFE_NAME.match(name) or name in {".", ".."}:
        raise ValueError("bad job name")
    if "\\" in name:
        raise ValueError("bad job name")
    home_resolved = home.resolve()
    p = (home / name).resolve()
    try:
        p.relative_to(home_resolved)
    except ValueError:
        raise ValueError("bad job name")
    return p


def list_jobs(home: Optional[Path]) -> list[dict]:
    """The jobs Mark has marked active, and only those.

    His real folder holds jobs going back years. Everything on disk is still
    shown when he opens Manage active jobs; this is the working list.
    """
    if home is None or not home.is_dir():
        return []
    active = set(workspace.active_jobs(home))
    out = [{"name": d.name, "photo_count": count_photos(d)}
           for d in sorted(home.iterdir())
           if d.is_dir() and not d.name.startswith(".") and d.name in active]
    return out


def list_all_folders(home: Optional[Path]) -> list[dict]:
    if home is None or not home.is_dir():
        return []
    out = [{"name": d.name, "photo_count": count_photos(d)}
           for d in sorted(home.iterdir()) if d.is_dir() and not d.name.startswith(".")]
    return out


def create_job(home: Path, name: str) -> dict:
    """Make the job folder and Mark's own eight folders inside it.

    A job the app makes is indistinguishable from one he made in Explorer.
    Folders the engine needs later (Old Report, Output, Legal, Improvements,
    Transcript information) are created by whatever needs them, so nothing
    unexplained ever appears on day one.
    """
    target = resolve_job(home, name)
    if target.exists():
        raise FileExistsError(name)
    home.mkdir(parents=True, exist_ok=True)
    for folder in MARK_FOLDERS:
        (target / folder).mkdir(parents=True, exist_ok=True)
    # He just made it, so he is working on it. Anything else would hide the
    # job he created behind a second step.
    workspace.save_active_jobs(home, workspace.active_jobs(home) + [name])
    return {"name": name}


def _parse_pipe_row(line: str) -> Optional[list]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    cells = [c.strip() for c in stripped[1:-1].split("|")]
    return cells


def brief_context(job: Path) -> str:
    """Pull Property address / Property type out of job-brief.md's Assignment
    pipe table (the format the firm's onboarding tooling actually writes),
    and combine them into one human-readable line.
    """
    # Named `path`, not `brief`: this module now imports the brief module,
    # and a local of the same name would shadow it inside this function.
    path = job / "job-brief.md"
    if not path.is_file():
        return ""

    address = ""
    prop_type = ""
    for line in path.read_text(errors="ignore").splitlines():
        cells = _parse_pipe_row(line)
        if not cells or len(cells) < 2:
            continue
        label = " ".join(cells[0].strip().lower().split())
        value = cells[1].strip()
        if not value or set(value) <= {"-"}:
            continue
        if label == "property address" and not address:
            address = value
        elif label == "property type" and not prop_type:
            prop_type = value

    if address and prop_type:
        return f"{address} · {prop_type}"
    return address or prop_type or ""


def job_detail(home: Path, name: str) -> dict:
    job = resolve_job(home, name)
    if not job.is_dir():
        raise FileNotFoundError(name)
    record = brief.read_brief(job)
    return {"name": name, "photo_count": count_photos(job),
            "context": brief_context(job),
            "engagement": record["fields"].get("Engagement type", ""),
            "sections": record["sections"]}

import datetime
import io
import json
import sys
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image

import applog
import brief
import busy
import captionbackup
import captions
import classify
import jobfacts
import jobs
import state
import thumbcache

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from photo_pages import exif_order  # noqa: E402

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:  # pragma: no cover - HEIC support optional in tests
    pass

router = APIRouter()
# Nothing writes here any more: thumbnails moved out of Mark's job folder and
# into app-owned storage. The name stays because a Photos folder from before
# that change still has one sitting in it, and it must go on being skipped
# rather than listed to him as a folder of his. Old caches are left alone.
THUMB_DIR = thumbcache.LEGACY_THUMB_DIR
THUMB_PX = 1024


def manifest_path(job: Path) -> Path:
    return jobs.photos_dir(job) / "photo-manifest.json"


def is_cut(entry: dict) -> bool:
    """Whether this photo has been cut from the report.

    Absent means included. That is the whole migration story for every
    manifest already on disk: a job written before this existed reads as all
    photos included, with nothing to convert and nothing to guess.
    """
    return bool(entry.get("cut"))


REVIEWED = "reviewed"


def is_reviewed(entry: dict) -> bool:
    """Whether Mark has looked at this caption and said so.

    A missing key means not reviewed. Every manifest written before review
    existed therefore reads as unreviewed, which is the safe direction: the
    app asks him to look rather than assuming he already did.
    """
    return bool(entry.get(REVIEWED))


def review_progress(manifest: dict) -> dict:
    """`8 of 12 reviewed`, counting only the photographs that are in.

    A photograph cut from the report needs no caption and no review, so it is
    outside both halves of the count.
    """
    rows = included(manifest)
    with_caption = [p for p in rows if str(p.get("caption", "")).strip()]
    done = [p for p in with_caption if is_reviewed(p)]
    outstanding = [p["file"] for p in rows if not is_reviewed(p)]
    return {
        "included": len(rows),
        "reviewed": len(done),
        "text": "%d of %d reviewed" % (len(done), len(rows)),
        "all_reviewed": not outstanding,
        "outstanding": outstanding,
    }


def reset_changed_reviews(existing: dict, incoming: dict) -> None:
    """Any caption whose words changed goes back to needing review.

    Editing a caption is the moment a reviewed one stops being reviewed, and
    it has to happen here rather than on the screen: the manifest is also
    hand-editable on disk, and a caption changed that way must not keep a tick
    it was given for different words.
    """
    was = {}
    for entry in (existing or {}).get("photos", []) or []:
        if isinstance(entry, dict) and entry.get("file"):
            was[entry["file"]] = str(entry.get("caption", ""))

    for entry in (incoming or {}).get("photos", []) or []:
        if not isinstance(entry, dict) or not entry.get("file"):
            continue
        before = was.get(entry["file"])
        now = str(entry.get("caption", ""))
        if before is not None and before != now:
            entry.pop(REVIEWED, None)


def included(manifest: dict) -> list:
    """The photos that go in the report, in order.

    One place, used by captions, by the preview and by the build, so those
    three can never disagree about which photos are in.
    """
    return [e for e in manifest.get("photos", []) if not is_cut(e)]


def _photo_files_on_disk(job: Path) -> list[Path]:
    """Every actual photo file sitting in the job's Photos folder right now,
    confined to that folder and confirmed to be a real file. The appraiser's
    actual workflow is dropping camera photos straight into the job folder,
    never through this app's own upload, so the manifest can never be
    trusted alone to know what's there -- the folder is the source of truth
    for *which* files exist.

    Skips the thumbnail cache directory and the manifest file itself, and
    uses the same allowed-extension set `jobs.count_photos` uses so the job
    card's count and this reconciliation never disagree on what counts as a
    photo.
    """
    return jobs.photo_files(job)


def _dir_entry_names(job: Path) -> set:
    """Bare names of every filesystem entry sitting directly in the Photos
    folder right now (any type, any extension), used only to decide whether
    an EXISTING manifest entry's file has been deleted.

    Deliberately not confinement- or extension-filtered: whether a name is
    *safe* is a separate question, already answered on every write and
    before every build by `_validate_manifest_shape` (which uses
    `_resolve_confined` itself). If this helper also filtered out unsafe
    names, a manifest entry pointing at a symlink that escapes the folder
    would look "deleted" and get silently dropped here -- laundering it
    past the security check instead of letting that check reject it with a
    clear error. This only answers "is a photo still there by this name."
    """
    return jobs.photo_names(job)


def photo_groups(job: Path) -> list:
    """Where this job keeps its photographs, so Mark can be asked which set is
    the report.

    His office keeps every shoot twice, full size and shrunk by hand, and the
    folder holding each varies job to job: `Original`, `Raw pics_`,
    `Minimized`, `full size`, `Building`, `Used`, `Reduced`, `Report Photos_`,
    or bare numbers. Nine conventions across eleven jobs, measured 2026-08-25,
    and a new helper in the office has just added a tenth. So nothing here
    reads a folder name for meaning. It counts what is where and lets him say.

    A group is the FULL folder path relative to `Photos`, empty for the top of
    `Photos` itself. Not the immediate child folder: Mason City's fifty chosen
    photographs and its seven rejected ones are two folders side by side inside
    one `Raw pics_` folder, and grouping by the child would hand him the seven
    he threw out.

    Biggest first, ties broken by name, so the set most likely to be the report
    is offered first and the same job asks the same question twice running.
    """
    counted: dict = {}
    for photo in jobs.photo_files(job):
        where = jobs.photo_folder(job, photo)
        if where not in counted:
            counted[where] = {"folder": where, "count": 0, "sample": photo.name}
        counted[where]["count"] += 1
    return sorted(counted.values(), key=lambda g: (-g["count"], g["folder"]))


SUBJECT_PHOTOGRAPH = "Subject photograph"


def _classified_in(job: Path) -> set:
    """Photographs Mark pulled in one at a time, as (folder, filename).

    His office sometimes leaves a straggler out of the folder it prepared, so
    the folder choice is a starting point and this is the top up. Only
    `Subject photograph` moves anything: a plat map is still a plat map.

    Records are keyed from the job root, so `Photos/Raw pics_X/one.jpeg`
    becomes ("Raw pics_X", "one.jpeg"). Anything outside `Photos` is not a
    photograph of the subject however it is labelled, and is ignored here.
    """
    picked = set()
    for rel, record in classify.for_job(job).items():
        if record.get("label") != SUBJECT_PHOTOGRAPH:
            continue
        parts = rel.split("/")
        if len(parts) < 2 or parts[0] != jobs.photos_dir(job).name:
            continue
        picked.add(("/".join(parts[1:-1]), parts[-1]))
    return picked


def _report_set(job: Path, entries: list) -> tuple:
    """Narrow the job's photographs to the ones that are in the report.

    Returns (photographs, chosen_folder, chosen_folder_is_missing).

    With no answer recorded, every photograph is in. That is what every job
    did before this existed and what a job with one folder of photographs
    still does, so nothing starts disappearing on its own: the screen asks the
    question, the manifest does not answer it by guessing.

    With an answer recorded, the report is that folder plus anything he
    classified in. If the folder he chose is no longer there, because the
    office renamed it, the answer is nothing and a flag saying so. It never
    falls back to another folder: a report quietly built from photographs he
    did not choose is exactly the confident wrong answer this app must not
    produce.
    """
    chosen = jobfacts.photo_folder(job)
    if chosen is None:
        return entries, None, False

    here = {str(e.get("folder") or "") for e in entries}
    missing = chosen not in here
    picked = _classified_in(job)
    kept = [e for e in entries
            if str(e.get("folder") or "") == chosen
            or (str(e.get("folder") or ""), e.get("file")) in picked]
    return kept, chosen, missing


def report_count(job: Path) -> int:
    """How many photographs this job's photo pages would be built from now.

    The job screen and the Photos screen have to agree. The job screen used to
    count every image in the Photos tree, which after Mark picks a folder is a
    different number from the one he is looking at: thirty three against
    sixteen, for the same section, on two screens. So this counts what would
    actually build, cuts taken off.

    Falls back to the plain count when the manifest cannot be read. A damaged
    photo-manifest.json is a real condition and it already has its own plain
    message on the Photos screen. It must not take the whole job screen down
    on the way past.
    """
    try:
        return len(included(load_manifest(job)))
    except Exception:
        return jobs.count_photos(job)


def load_manifest(job: Path) -> dict:
    """Load the manifest and reconcile it against what's actually in the
    Photos folder before returning it.

    A human's ordering and captions are never reshuffled: existing entries
    keep their position and wording as long as their file still exists.
    Files sitting on disk that the manifest doesn't know about are appended
    at the end, in EXIF capture order, with an empty caption. Entries whose
    file has been deleted are dropped so a missing photo can't break the
    build.

    This never writes back to disk -- callers that need the reconciled
    result persisted (upload, captions) save explicitly after calling this;
    a plain GET must not have a side effect.
    """
    p = manifest_path(job)
    if p.is_file():
        # Hand-editable by design, so broken JSON is an expected condition,
        # not a crash. Same answer _set_cut and clear_captions already give.
        try:
            manifest = json.loads(p.read_text())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="photo-manifest.json is not valid JSON. "
                       "Fix the file or delete it and try again.")
        if not isinstance(manifest, dict):
            raise HTTPException(
                status_code=400,
                detail="photo-manifest.json should be a JSON object, "
                       "not a list or a bare value.")
    else:
        manifest = {
            "job": job.name,
            "context": jobs.brief_context(job),
            "report_year": datetime.date.today().year,
            "photos": [],
        }

    # Which caption style this job writes in. Only ever filled in when absent,
    # so a style Mark picked is never re-guessed from the property type on a
    # later load. His choice outranks the suggestion, permanently.
    if not manifest.get("caption_style"):
        prop_type = brief.read_brief(job)["fields"].get("Property type", "")
        manifest["caption_style"] = captions.default_style(prop_type)

    on_disk = _photo_files_on_disk(job)
    still_present = _dir_entry_names(job)

    kept = [entry for entry in manifest.get("photos", [])
            if isinstance(entry, dict) and entry.get("file") in still_present]

    # Where each photograph actually sits now, by name. A manifest written
    # before subfolders were read carries no folder at all, and one Mark has
    # since moved into `Original` would otherwise resolve to a path that is no
    # longer there. The folder is corrected from the tree; his caption, his
    # order and his tick are never touched.
    where = {f.name: jobs.photo_folder(job, f) for f in on_disk}
    for entry in kept:
        found = where.get(entry.get("file"))
        if found is None:
            continue
        if found:
            entry["folder"] = found
        else:
            entry.pop("folder", None)

    known = {entry["file"] for entry in kept}
    new_files = [f for f in on_disk if f.name not in known]
    if new_files:
        # The expensive step: one open per file, to read its capture date.
        # Logged by name, because this is the number that settles whether a
        # slow open is this or something else on his network drive.
        started = time.monotonic()
        ordered = exif_order(new_files)
        elapsed_ms = round((time.monotonic() - started) * 1000)
        applog.note("reading capture dates", job=job.name,
                    files=len(new_files), ms=elapsed_ms)
    else:
        ordered = []
    for f in ordered:
        entry = {"file": f.name, "caption": ""}
        folder = jobs.photo_folder(job, f)
        if folder:
            entry["folder"] = folder
        kept.append(entry)

    # Everything on disk has now been reconciled, so his captions, his order
    # and his ticks are all accounted for. Only now is the list narrowed to
    # the report. The file on disk still holds every photograph; this is the
    # view, and save_manifest below is what keeps the two from diverging.
    in_report, chosen, missing = _report_set(job, kept)
    manifest["photos"] = in_report
    manifest["photo_folder"] = chosen
    manifest["photo_folder_missing"] = missing
    return manifest


def save_manifest(job: Path, manifest: dict):
    """Write the manifest, keeping every photograph the caller was not shown.

    The screen only ever holds the photographs in the report, so what comes
    back from it is only those. Writing that straight over the file would
    throw away every caption he had typed on a photograph currently outside
    the chosen folder, and he would never see it go.

    So entries already on disk that the caller did not carry are kept, in
    their existing order, after the ones it did. Nothing he typed is lost by
    changing his mind about which folder the report comes from.
    """
    jobs.photos_dir(job).mkdir(parents=True, exist_ok=True)
    path = manifest_path(job)

    out = dict(manifest)
    # The view's own bookkeeping. Recomputed on every read, so storing it
    # would only create a second copy to go stale.
    out.pop("photo_folder", None)
    out.pop("photo_folder_missing", None)

    coming = [e for e in out.get("photos", []) if isinstance(e, dict)]
    known = {e.get("file") for e in coming}
    kept_back = []
    existing_text = None
    if path.is_file():
        existing_text = path.read_text()
        try:
            existing = json.loads(existing_text)
        except ValueError:
            existing = {}
        if isinstance(existing, dict):
            kept_back = [e for e in existing.get("photos", []) or []
                         if isinstance(e, dict) and e.get("file") not in known]
    out["photos"] = coming + kept_back

    # The version from just before this write, kept outside the job folder.
    # Nothing here can stop the save that follows: keeping the spare must
    # never be the reason a caption fails to save.
    if existing_text is not None:
        captionbackup.keep(jobs.photos_dir(job), existing_text)

    state.write_text(path, json.dumps(out, indent=2))


def _resolve_confined(path: Path, base: Path) -> Optional[Path]:
    """Resolve `path` (following any symlinks) and confirm it still lives
    inside the resolved `base` directory. Returns the resolved Path if it
    does, or None if it escapes.

    `Path(...).name` alone only confines the *string* -- it stops a
    filename from carrying literal '../' or an embedded separator, but it
    does nothing about a filename that exists on disk as a symlink pointing
    somewhere else entirely. `Path.resolve()` follows symlinks and
    normalizes '..' the same way on POSIX and Windows, so comparing the
    resolved target against the resolved base with `relative_to` catches
    both attack shapes with one check.
    """
    resolved_base = base.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_base)
    except ValueError:
        return None
    return resolved


def _is_occupied(p: Path) -> bool:
    """True if anything already sits at `p`, including a symlink -- broken
    or not. `Path.exists()` alone follows symlinks and reports False for a
    *dangling* one (target doesn't exist), which would let `free_name`
    believe a pre-planted broken symlink's name is free to use. `.name`
    picks it up regardless of where, or whether, it points.
    """
    return p.is_symlink() or p.exists()


def free_name(d: Path, name: str, taken=frozenset()) -> str:
    """A name nothing else in the Photos tree is using.

    `taken` carries the names already in use in subfolders. Without it an
    upload could take a name a photograph in `Original` already has, and the
    walk -- which keeps the first of any repeated name -- would then list the
    upload and quietly hide the other one.
    """
    stem, suffix = Path(name).stem, Path(name).suffix
    candidate, n = name, 2
    while _is_occupied(d / candidate) or candidate.lower() in taken:
        candidate, n = f"{stem} ({n}){suffix}", n + 1
    return candidate


def _confine_write_target(target: Path, photos: Path) -> None:
    """Defense in depth alongside `_is_occupied`: refuse to write anywhere
    that doesn't resolve inside the job's Photos folder. `target` should
    never already exist at this point (`free_name` only hands back
    unoccupied names, and `_is_occupied` now treats any symlink -- dangling
    or not -- as occupied), so this is the same containment check `thumb()`
    applies on the read side, applied here before bytes ever touch disk.
    """
    if _resolve_confined(target, photos) is None:
        raise HTTPException(400, "Upload target escaped the Photos folder.")


def store_upload(job: Path, upload: UploadFile) -> str:
    photos = jobs.photos_dir(job)
    photos.mkdir(parents=True, exist_ok=True)
    taken = {p.name.lower() for p in jobs.photo_files(job)}
    raw = upload.file.read()
    # .name confines an untrusted filename (which may carry ../, an absolute
    # path, or backslash traversal forms) to its final path component only,
    # so it can never resolve outside this job's Photos folder.
    name = Path(upload.filename or "photo.jpg").name
    if name.lower().endswith(".heic"):
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        name = Path(name).with_suffix(".jpg").name
        target = photos / free_name(photos, name, taken)
        _confine_write_target(target, photos)
        img.save(target, format="JPEG", quality=92)
    else:
        target = photos / free_name(photos, name, taken)
        _confine_write_target(target, photos)
        target.write_bytes(raw)
    return target.name


def _job_or_404(name: str) -> Path:
    home = jobs.jobs_home()
    if home is None:
        # Not the same thing as a missing job, and not worth pretending it is.
        raise HTTPException(400, "No jobs folder chosen yet.")
    try:
        job = jobs.resolve_job(home, name)
    except ValueError:
        raise HTTPException(404, "Job not found.")
    if not job.is_dir():
        raise HTTPException(404, "Job not found.")
    return job


def _validate_manifest_shape(job: Path, manifest) -> Optional[str]:
    """Return a plain-English error if `manifest` isn't shaped like the
    engine's contract, or if any photo entry's `file` could make the engine
    (photo_pages.build_photo_docx, which does `photos_dir / entry["file"]`
    with no checks of its own) read a file outside this job's Photos
    folder. Returns None when the payload is safe to save.

    Deliberately narrow: this checks exactly the two things that matter for
    path safety (bare filename, resolves inside Photos/) plus the minimum
    shape the engine needs (a "photos" list of file-bearing objects) -- it
    is not a general schema validator.
    """
    if not isinstance(manifest, dict):
        return "Manifest must be a JSON object."
    photos = manifest.get("photos")
    if not isinstance(photos, list):
        return "Manifest 'photos' must be a list."
    photos_dir = jobs.photos_dir(job)
    for entry in photos:
        if not isinstance(entry, dict):
            return "Each entry in 'photos' must be an object."
        name = entry.get("file")
        if not isinstance(name, str) or not name:
            return "Each photo entry needs a non-empty 'file' name."
        if name != Path(name).name:
            return f"Photo file name {name!r} must be a bare filename with no path separators."
        folder = entry.get("folder", "")
        if not isinstance(folder, str):
            return "A photo's 'folder' must be text."
        if folder and ("\\" in folder or folder.startswith("/")
                       or ".." in folder.split("/")):
            return f"Photo folder {folder!r} must be a plain subfolder of Photos."
        if _resolve_confined(jobs.photo_path(job, entry), photos_dir) is None:
            return f"Photo file name {name!r} resolves outside the Photos folder."
        if REVIEWED in entry and not isinstance(entry[REVIEWED], bool):
            return "A photo's reviewed flag must be true or false."
        if "cut" in entry and not isinstance(entry["cut"], bool):
            return "A photo's 'cut' must be true or false."
    return None


@router.post("/api/jobs/{name}/photos")
def upload_photos(name: str, files: list[UploadFile]):
    job = _job_or_404(name)
    with busy.writing():
        manifest = load_manifest(job)
        known = {p["file"] for p in manifest["photos"]}
        stored = [store_upload(job, f) for f in files]
        fresh = [n for n in stored if n not in known]
        ordered = exif_order([jobs.photos_dir(job) / n for n in fresh])
        manifest["photos"].extend({"file": p.name, "caption": ""} for p in ordered)
        save_manifest(job, manifest)
    return manifest


@router.get("/api/jobs/{name}/manifest")
def get_manifest(name: str):
    return load_manifest(_job_or_404(name))


@router.put("/api/jobs/{name}/manifest")
def put_manifest(name: str, manifest: dict):
    job = _job_or_404(name)
    error = _validate_manifest_shape(job, manifest)
    if error:
        raise HTTPException(400, error)
    # An edited caption is no longer the caption he reviewed, so the tick comes
    # off here, against what is actually on disk, rather than being trusted to
    # whatever sent this.
    reset_changed_reviews(load_manifest(job), manifest)
    with busy.writing():
        save_manifest(job, manifest)
    return {"ok": True, "review": review_progress(manifest)}


def _set_reviewed(job: Path, file: str, reviewed: bool) -> dict:
    """Tick or untick one caption. Touches that one key and nothing else."""
    manifest = load_manifest(job)
    name = Path(file).name
    for entry in manifest["photos"]:
        if entry.get("file") == name:
            if reviewed:
                if not str(entry.get("caption", "")).strip():
                    raise HTTPException(400, "Write a caption before marking it reviewed.")
                entry[REVIEWED] = True
            else:
                entry.pop(REVIEWED, None)
            with busy.writing():
                save_manifest(job, manifest)
            return {**manifest, "review": review_progress(manifest)}
    raise HTTPException(404, "That photo is not in this job.")


@router.post("/api/jobs/{name}/photos/{file}/reviewed")
def mark_reviewed(name: str, file: str):
    """One click, one caption. Deliberately not called Approve, and there is
    deliberately no way to do all of them at once."""
    return _set_reviewed(_job_or_404(name), file, True)


@router.post("/api/jobs/{name}/photos/{file}/unreviewed")
def mark_unreviewed(name: str, file: str):
    """Undo the tick. The same click again, so nothing is a trap."""
    return _set_reviewed(_job_or_404(name), file, False)


def _set_cut(job: Path, file: str, cut: bool) -> dict:
    """Mark one photo cut or bring it back. Touches that one key, nothing else.

    The entry keeps its place in the list, which is what makes bringing it
    back free: its position was never lost, so there is nothing to restore
    it to. Bringing back removes the key rather than writing false, so a
    manifest never accumulates a field that means the default.
    """
    path = manifest_path(job)
    if not path.is_file():
        # No list on disk yet is not an error, it is a job he has just opened.
        # Nothing writes the manifest until he types a caption or reorders, so
        # taking a photograph out could be the first thing he ever does in a
        # job, and it used to answer "This job has no photo list yet". Build
        # already reconciles rather than refusing here; this now does the same.
        manifest = load_manifest(job)
    else:
        try:
            manifest = json.loads(path.read_text())
        except ValueError:
            raise HTTPException(400, "This job's photo list could not be read.")

    error = _validate_manifest_shape(job, manifest)
    if error:
        raise HTTPException(400, error)

    bare = Path(file).name
    for entry in manifest["photos"]:
        if entry.get("file") == bare:
            if cut:
                entry["cut"] = True
            else:
                entry.pop("cut", None)
            break
    else:
        raise HTTPException(404, "That photo is not in this job.")

    with busy.writing():
        save_manifest(job, manifest)
    return load_manifest(job)


@router.post("/api/jobs/{name}/photos/{file}/cut")
def cut_photo(name: str, file: str):
    """Take a photo out of the report. The file on disk is not touched."""
    return _set_cut(_job_or_404(name), file, True)


@router.post("/api/jobs/{name}/photos/{file}/uncut")
def uncut_photo(name: str, file: str):
    """Put it back, in the place it always held."""
    return _set_cut(_job_or_404(name), file, False)


@router.post("/api/jobs/{name}/captions/clear")
def clear_captions(name: str):
    """Blank every caption in this one job, and change nothing else.

    Reads the manifest file straight off disk rather than through
    load_manifest, so no reconciliation runs and nothing is added or
    dropped on the way past. Every other key is written back exactly as it
    was found, including keys this code does not know about: a manifest
    that has been round-tripped through the browser carries whatever the
    API answered with, and `ai_available` has been seen sitting in a real
    one on disk.

    Deliberately not a delete of the manifest. The manifest also holds the
    photo order, the caption style Mark chose, the report year and the
    context line, and deleting it would throw all of that away to remove
    captions.
    """
    job = _job_or_404(name)
    path = manifest_path(job)
    if not path.is_file():
        raise HTTPException(400, "There are no captions to clear.")

    try:
        manifest = json.loads(path.read_text())
    except ValueError:
        raise HTTPException(400, "This job's photo list could not be read.")

    error = _validate_manifest_shape(job, manifest)
    if error:
        raise HTTPException(400, error)

    cleared = sum(1 for entry in manifest["photos"]
                  if str(entry.get("caption", "")).strip())
    if not cleared:
        raise HTTPException(400, "There are no captions to clear.")

    with busy.writing():
        for entry in manifest["photos"]:
            entry["caption"] = ""
        save_manifest(job, manifest)
    return {"cleared": cleared, **load_manifest(job)}


def _where_it_sits(job: Path, photos_dir: Path, bare: str) -> Optional[Path]:
    """This photograph's path, asked of the manifest before the folder.

    Mark's jobs are on a mapped network drive, so every filesystem question is
    a request to another machine and the cost of a screen is the number of
    questions, not the work. This route used to answer "where is this
    photograph" by walking the whole Photos tree, once per thumbnail. Measured
    2026-08-26 on Mason City: 57 photographs, 57 walks, 6,954 path lookups for
    one screen. A tenth of a second here and up to thirty-five seconds there.

    The app already recorded where each photograph sits when it built the
    manifest, so the first answer is a file read. The tree walk stays as the
    fallback for a photograph the manifest has never seen, which is a
    photograph he dropped into the folder a moment ago, so nothing that used to
    appear stops appearing.

    The manifest is hand-editable, so the path it yields is confined and
    checked exactly the way the walk's own answer always was. It is a hint
    about where to look, never permission to read something.
    """
    path = manifest_path(job)
    if path.is_file():
        try:
            saved = json.loads(path.read_text())
        except ValueError:
            saved = None
        if isinstance(saved, dict):
            for entry in saved.get("photos", []) or []:
                if not isinstance(entry, dict) or entry.get("file") != bare:
                    continue
                folder = entry.get("folder", "")
                if not isinstance(folder, str):
                    break
                guess = _resolve_confined(jobs.photo_path(job, entry), photos_dir)
                if guess is not None and guess.is_file():
                    return guess
                break

    found = next((p for p in jobs.photo_files(job) if p.name == bare), None)
    if found is None:
        return None
    src = _resolve_confined(found, photos_dir)
    return src if src is not None and src.is_file() else None


@router.get("/api/jobs/{name}/thumb/{file}")
def thumb(name: str, file: str):
    job = _job_or_404(name)
    photos_dir = jobs.photos_dir(job)
    # Path(...).name confines the *string* (../, absolute path, backslash
    # form all collapse to a bare final component); _resolve_confined then
    # confines the *real, on-disk* target, so a symlink planted inside
    # Photos/ that points outside it is caught too -- both is_file() and
    # Image.open() below follow symlinks, so the string check alone is not
    # enough.
    # A photograph's filename is unique across the whole Photos tree, because
    # the walk drops a repeat, so the bare name in the URL still names exactly
    # one file wherever it sits.
    bare = Path(file).name
    src = _where_it_sits(job, photos_dir, bare)
    if src is None:
        raise HTTPException(404, "Photo not found.")
    # App-owned storage, outside his job folder. See thumbcache.py.
    cached = thumbcache.cached_file(photos_dir, file)
    if thumbcache.is_stale(cached, src):
        cached.parent.mkdir(parents=True, exist_ok=True)
        img = Image.open(src).convert("RGB")
        img.thumbnail((THUMB_PX, THUMB_PX))
        img.save(cached, format="JPEG", quality=85)
    return Response(cached.read_bytes(), media_type="image/jpeg")

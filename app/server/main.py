import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from typing import Optional

from pydantic import BaseModel

import brief
import browse
import busy
import captions
import classify
import inventory
import jobs
import packaging
import sections
import settings
import state
import workspace

# Spenser's testing tool, and the one module that is not in the package Mark
# receives. It is excluded there, so this import has to be allowed to fail:
# without the guard, removing the file stops the whole server importing and the
# app does not start at all on his machine. `demo.enabled()` already gated the
# button and the endpoint, so absence is the second half of the same answer,
# not a new one.
try:
    import demo
except ImportError:                                  # pragma: no cover - see test_packaged_app
    demo = None

# Ships inside the app. It used to be read out of the client corpus, which
# only exists on the development Mac, so the first press of Build photo pages
# on Mark's PC would have failed. RRF_PHOTO_TEMPLATE still overrides it.
DEFAULT_PHOTO_TEMPLATE = (
    Path(__file__).resolve().parents[1] / "templates" / "Photo.docx"
)


def photo_pages_per_table() -> int:
    """How many photos share one printed page, read from the engine rather
    than restated, so a preview always shows exactly one page."""
    from photo_pages import PHOTOS_PER_TABLE
    return PHOTOS_PER_TABLE


class NewJob(BaseModel):
    name: str


class SectionChoice(BaseModel):
    sections: list[str]


class NewKey(BaseModel):
    key: str


class NewFolder(BaseModel):
    path: str


class ActiveJobs(BaseModel):
    active: list[str]


class Classification(BaseModel):
    file: str
    label: str


class FileOnly(BaseModel):
    file: str


class ProposeName(BaseModel):
    city: str = ""
    street: str = ""
    engagement: str = ""
    # Optional[int], not int | None: the newer spelling needs Python 3.10,
    # and nobody has checked what is on Mark's Windows machine yet.
    year: Optional[int] = None


class Intake(BaseModel):
    name: str
    street: str = ""
    city: str = ""
    state: str = "Iowa"
    property_type: str = ""
    engagement: str = ""
    client: str = ""
    intended_use: str = ""
    effective_date: str = ""
    due_date: str = ""
    file_number: str = ""


def create_app() -> FastAPI:
    app = FastAPI(title="Roy R. Fisher App")

    from fastapi.responses import JSONResponse

    @app.exception_handler(busy.Busy)
    def busy_handler(_request, exc: busy.Busy):
        """409, and a sentence saying nothing happened. Never a silent retry."""
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(state.StateUnreadable)
    def state_unreadable_handler(_request, exc: state.StateUnreadable):
        """One of the app's own files is damaged. Say so in a sentence.

        409 rather than 500: nothing crashed and nothing is broken in the code,
        a file on disk cannot be trusted and the app declined to guess. The
        body carries the approved sentence and never the traceback, the path,
        or the JSON parser's own words. The technical reason stays on the
        exception for tests and for Spenser.

        Silence was the old behaviour and it was worse than an error: a
        damaged settings file read as "he has not chosen a jobs folder yet",
        which is the first-run screen, so the app appeared to have forgotten
        his setup and offered no hint that anything had been lost.

        `state_unreadable` is a flag for the screen, not a message. 409 alone
        is not enough to identify this: `busy.Busy` answers 409 too, and the
        screen would have to tell them apart by matching the sentence, which
        would mean keeping a second copy of that sentence in JavaScript for it
        to drift away from. The flag says which case this is; the sentence
        stays in one place.
        """
        return JSONResponse(status_code=409,
                            content={"detail": exc.message,
                                     "state_unreadable": True})

    if demo is not None:
        @app.exception_handler(demo.DemoError)
        def demo_error_handler(_request, exc: demo.DemoError):
            """A reset that did not finish says so, and says where everything
            is. It never reports a success it has not verified."""
            return JSONResponse(status_code=500,
                                content={"detail": exc.message, **exc.report})

    def home_or_400() -> Path:
        """The jobs folder, or a plain refusal. Nothing in the app invents
        one: if he has not chosen yet, every job route says so."""
        home = jobs.jobs_home()
        if home is None:
            raise HTTPException(400, "No jobs folder chosen yet.")
        return home

    @app.get("/api/version")
    def app_version():
        """Which version is answering on this port.

        Three jobs, and it is the same answer to all of them. The screens show
        it, so Mark can tell which folder he launched. The launcher probes it
        to decide whether the thing on a port is us, which `/api/demo` could
        never do because the demo routes are excluded from what he receives.
        And it is what the last-good record is checked against before a version
        is written down as one that started.

        Empty when there is no VERSION file, which is what a checkout without
        one looks like. Never guessed at.
        """
        return {"version": packaging.version_of(
            Path(__file__).resolve().parents[2])}

    if demo is not None:
        @app.get("/api/demo")
        def demo_status():
            """Whether the testing tool is configured on this computer. On
            Mark's machine the module is not there at all, so neither route is
            registered and the button never renders."""
            return demo.status()

        @app.post("/api/demo/reset")
        def demo_reset():
            if not demo.enabled():
                raise HTTPException(404, "Not found.")
            with busy.resetting():
                return demo.reset()

    @app.get("/api/browse")
    def browse_folders(path: str = ""):
        """Folders directly inside `path`. Reads nothing else and guesses
        nothing. No path means start where he lives."""
        return browse.listing(path)

    @app.get("/api/workspace")
    def read_workspace():
        return workspace.status()

    @app.get("/api/workspace/folders")
    def workspace_folders():
        """Every immediate child folder of the chosen parent, by exact name,
        and which of them he has marked active."""
        home = home_or_400()
        facts = workspace.describe(home)
        if not facts["readable"]:
            raise HTTPException(400, "That folder cannot be opened on this computer.")
        try:
            on_disk = workspace.child_folder_names(home)
        except OSError:
            raise HTTPException(400, "That folder cannot be opened on this computer.")
        active = workspace.active_jobs(home)
        return {"parent": str(home), "folders": on_disk, "active": active,
                # Names he marked active that are no longer on disk. Reported
                # by name, never quietly dropped and never matched to some
                # other folder that happens to be new.
                "missing": sorted(set(active) - set(on_disk))}

    @app.put("/api/workspace/folders")
    def save_workspace_folders(body: ActiveJobs):
        home = home_or_400()
        with busy.writing():
            workspace.save_active_jobs(home, body.active)
        return {"active": workspace.active_jobs(home)}

    @app.put("/api/workspace")
    def save_workspace(body: NewFolder):
        path = body.path
        if not path.strip():
            raise HTTPException(400, "No folder was chosen.")
        # Looked at again here, not trusted from the pick. He may have moved
        # or deleted it between choosing and confirming.
        facts = workspace.describe(Path(path))
        if not facts["exists"]:
            raise HTTPException(400, "That folder is not there any more.")
        if not facts["is_folder"]:
            raise HTTPException(400, "That is a file, not a folder.")
        if not facts["readable"]:
            raise HTTPException(400, "That folder cannot be opened on this computer.")
        with busy.writing():
            workspace.save_folder(path)
        # Nothing to restart: every route reads the saved answer when asked.
        return workspace.status()

    @app.delete("/api/workspace")
    def forget_workspace():
        """Start setup over. Forgets the folder and touches nothing else.

        No job folder, no job file and no key is opened. Every route reads
        the saved answer when asked, so the screens fall back to the opening
        question at once with nothing restarted.
        """
        with busy.writing():
            workspace.forget_folder()
        return workspace.status()

    @app.get("/api/jobs")
    def list_jobs():
        return jobs.list_jobs(jobs.jobs_home())

    @app.post("/api/jobs")
    def create_job(body: NewJob):
        try:
            with busy.writing():
                return jobs.create_job(home_or_400(), body.name)
        except ValueError:
            raise HTTPException(400, "That job name can't be used as a folder name.")
        except FileExistsError:
            raise HTTPException(409, "A job with that name already exists.")

    @app.post("/api/intake/propose-name")
    def propose_name(body: ProposeName):
        import datetime
        year = body.year or datetime.date.today().year
        return {"name": jobs.propose_folder_name(body.city, body.street, body.engagement, year)}

    @app.post("/api/intake")
    def intake(body: Intake):
        # These four decide the folder name, which donors apply, and which
        # sections the report needs. Everything else can arrive later,
        # because at intake Mark often does not have it yet.
        for value, message in (
            (body.street, "Enter the street address."),
            (body.city, "Enter the city."),
            (body.property_type, "Choose a property type."),
            (body.engagement, "Choose a kind of appraisal."),
        ):
            if not value.strip():
                raise HTTPException(400, message)
        if body.engagement not in sections.ENGAGEMENTS:
            raise HTTPException(400, "That is not one of the kinds of appraisal.")

        home = home_or_400()
        with busy.writing():
            try:
                jobs.create_job(home, body.name)
            except ValueError:
                raise HTTPException(400, "That folder name can't be used. Try a simpler one.")
            except FileExistsError:
                raise HTTPException(409, "A job with that name already exists.")

            job = jobs.resolve_job(home, body.name)
            address = ", ".join(p for p in [body.street.strip(), body.city.strip(),
                                            body.state.strip()] if p)
            brief.write_brief(job, {
                "Property address": address,
                "Property type": body.property_type,
                "Engagement type": body.engagement,
                "Client (intended user)": body.client,
                "Intended use": body.intended_use,
                "Effective date of value": body.effective_date,
                "Report due date": body.due_date,
                "Office file number": body.file_number,
            }, sections=[])
        return {"name": body.name}

    @app.get("/api/jobs/{name}")
    def job_detail(name: str):
        try:
            return jobs.job_detail(home_or_400(), name)
        except (FileNotFoundError, ValueError):
            raise HTTPException(404, "Job not found.")

    import photos as photos_routes
    app.include_router(photos_routes.router)

    @app.get("/api/jobs/{name}/sections")
    def get_sections(name: str):
        job = photos_routes._job_or_404(name)
        record = brief.read_brief(job)
        engagement = record["fields"].get("Engagement type", "").strip()
        chosen = record["sections"]

        try:
            proposal = sections.propose(engagement)
        except (ValueError, FileNotFoundError):
            # No engagement type yet, or a shape the matrix does not cover.
            # Say so rather than proposing a full appraisal by default.
            return {"engagement": engagement, "thin_evidence": False,
                    "chosen": bool(chosen),
                    "sections": [{"name": s, "default": False, "chosen": True} for s in chosen]}

        rows = []
        seen = set()
        for entry in proposal["sections"]:
            seen.add(entry["name"])
            rows.append({"name": entry["name"], "default": entry["default"],
                         "chosen": entry["name"] in chosen if chosen else entry["default"]})
        # Anything Mark added that the matrix does not know about is kept and
        # shown, never silently dropped.
        for extra in chosen:
            if extra not in seen:
                rows.append({"name": extra, "default": False, "chosen": True})

        return {"engagement": engagement, "thin_evidence": proposal["thin_evidence"],
                "chosen": bool(chosen), "sections": rows}

    @app.get("/api/settings")
    def read_settings():
        return settings.status()

    @app.put("/api/settings/key")
    def save_settings_key(body: NewKey):
        key = body.key.strip()
        if not key:
            raise HTTPException(400, "Paste your key in first.")

        checked, message = True, "Saved. Reading letters and writing captions are on."
        try:
            settings.check_key(key)
        except settings.BadKey as exc:
            # Never store a key the service has already refused.
            raise HTTPException(400, f"{exc}. Check you copied the whole thing, then try again.")
        except Exception:
            checked = False
            message = ("Saved, but we could not reach Anthropic to check it. "
                       "If captions do not work, come back and paste it again.")

        settings.save_key(key)
        return {**settings.status(), "checked": checked, "message": message}

    @app.delete("/api/settings/key")
    def delete_settings_key():
        settings.remove_key()
        return {**settings.status(),
                "message": "Removed. You can still type captions in yourself."}

    @app.get("/api/caption-styles")
    def caption_styles():
        # The screen draws its samples from here rather than restating them,
        # so what Mark is shown can never drift from what the model is told.
        return {"ai_available": captions.ai_available(),
                "styles": [
                    {"key": key, "label": s["label"], "sample": s["sample"],
                     "note": s["note"], "thin_evidence": s["thin_evidence"]}
                    for key, s in captions.STYLES.items()
                ]}

    @app.get("/api/classifications")
    def classification_labels():
        # The screen draws its menu from here rather than restating the list,
        # so what Mark can pick can never drift from what the server accepts.
        return {"labels": list(classify.LABELS)}

    @app.get("/api/jobs/{name}/folders")
    def job_folders(name: str):
        job = photos_routes._job_or_404(name)
        return classify.attach(job, inventory.read_job(job))

    @app.put("/api/jobs/{name}/classification")
    def put_classification(name: str, body: Classification):
        job = photos_routes._job_or_404(name)
        try:
            record = classify.set_label(job, body.file, body.label)
        except ValueError:
            raise HTTPException(400, "That is not one of the classifications.")
        except LookupError:
            # Not there now, whatever it was a moment ago. Recording an answer
            # about a file the app cannot see would be a claim it cannot check.
            raise HTTPException(404, "That file is not in this job.")
        return {"file": body.file, "label": record["label"], "state": "present"}

    @app.delete("/api/jobs/{name}/classification")
    def delete_classification(name: str, body: FileOnly):
        # Works whether or not the file is still there, which is how a record
        # for something he has since renamed gets cleared. Only the app's own
        # note goes; the file, if it exists, is left exactly as it is.
        classify.remove_label(photos_routes._job_or_404(name), body.file)
        return {"ok": True}

    @app.put("/api/jobs/{name}/sections")
    def put_sections(name: str, body: SectionChoice):
        job = photos_routes._job_or_404(name)
        with busy.writing():
            brief.write_brief(job, {}, sections=[s.strip() for s in body.sections if s.strip()])
        return {"ok": True}

    @app.post("/api/jobs/{name}/captions")
    def draft_job_captions(name: str):
        job = photos_routes._job_or_404(name)
        manifest = photos_routes.load_manifest(job)
        if not captions.ai_available():
            return {**manifest, "ai_available": False}

        # Never trust a filename string from the manifest: resolve the real
        # path and confirm it stays inside this job's Photos folder before
        # handing it to draft_captions() to open. Reuses photos.py's own
        # confinement helper rather than a parallel path check.
        photos_dir = jobs.photos_dir(job)
        blanks = []
        for p in photos_routes.included(manifest):
            if p["caption"].strip():
                continue
            candidate = photos_dir / Path(p["file"]).name
            resolved = photos_routes._resolve_confined(candidate, photos_dir)
            if resolved is not None and resolved.is_file():
                blanks.append(resolved)

        if blanks:
            drafted = captions.draft_captions(
                manifest.get("context", ""), blanks,
                style=manifest.get("caption_style", captions.DEFAULT_STYLE))
            # Only the write is guarded. Asking the model takes real seconds
            # and holding the floor for all of it would make a reset wait on
            # the network.
            with busy.writing():
                for p in photos_routes.included(manifest):
                    if not p["caption"].strip():
                        p["caption"] = drafted.get(p["file"], "")
                photos_routes.save_manifest(job, manifest)

        return {**manifest, "ai_available": True}

    @app.post("/api/jobs/{name}/caption-preview")
    def preview_captions(name: str):
        """Caption one page's worth of this job's own photos, both ways.

        A look, not a decision: nothing here is saved. The screen shows the
        result so Mark is choosing between two real sentences about his own
        building rather than two abstract examples.
        """
        job = photos_routes._job_or_404(name)
        manifest = photos_routes.load_manifest(job)
        # One page is three photos, so that is what the preview shows.
        sample = photos_routes.included(manifest)[:photo_pages_per_table()]
        names = [p["file"] for p in sample]
        if not names or not captions.ai_available():
            return {"ai_available": False, "photos": names, "captions": {}}

        photos_dir = jobs.photos_dir(job)
        paths = []
        for entry in sample:
            resolved = photos_routes._resolve_confined(
                photos_dir / Path(entry["file"]).name, photos_dir)
            if resolved is not None and resolved.is_file():
                paths.append(resolved)

        drafted = {}
        for style in captions.STYLES:
            try:
                drafted[style] = captions.draft_captions(
                    manifest.get("context", ""), paths, style=style)
            except Exception as exc:
                raise HTTPException(502, f"Could not write the sample captions: {type(exc).__name__}")
        return {"ai_available": True, "photos": names, "captions": drafted}

    @app.post("/api/jobs/{name}/build")
    def build_photos(name: str):
        job = photos_routes._job_or_404(name)
        manifest_file = photos_routes.manifest_path(job)
        manifest_existed = manifest_file.is_file()

        # The appraiser's real workflow is dropping camera photos straight
        # into the job folder and then opening the app to hit Build --
        # often before the app has ever written a manifest file for this
        # job. Checking manifest_file.is_file() first told him "No photos
        # yet" even when photos were sitting right there. Reconcile against
        # the folder the same way GET /manifest does (load_manifest keeps
        # every existing entry's position and caption, only appends
        # newly-found files and drops ones that vanished) and refuse only
        # when that reconciliation still comes up with nothing to build.
        manifest = photos_routes.load_manifest(job)
        if not manifest["photos"]:
            raise HTTPException(400, "No photos yet. Drop photos in first.")
        # Every photo cut is a legitimate state, and reversible, so it is
        # refused here rather than forbidden at the moment of cutting.
        if not photos_routes.included(manifest):
            raise HTTPException(400, "Bring back at least one photo to build the report.")

        # The manifest file sits on disk where a human or another process
        # can edit it directly, bypassing PUT /manifest and its
        # validation entirely. Re-validate here with the same
        # resolve-based helper PUT uses, before handing the manifest to
        # the engine (photo_pages.build_photo_docx does
        # `photos_dir / entry["file"]` with no checks of its own) -- never
        # trust that the PUT path was the only writer.
        error = photos_routes._validate_manifest_shape(job, manifest)
        if error:
            raise HTTPException(400, error)

        if not manifest_existed:
            # build_photo_docx (below) reads manifest_file straight off
            # disk, not this in-memory reconciliation, so a job with no
            # manifest file yet needs one written before the engine can
            # read anything at all. load_manifest() never reorders existing
            # entries or rewrites a caption -- it only appends newly-found
            # files in EXIF order with a blank caption -- so this cannot
            # clobber a human's work. When a manifest file already existed,
            # it is deliberately left untouched: the engine reading the raw
            # file rather than this reconciliation is what makes a
            # genuinely dangling photos[].file entry surface as a specific,
            # honest build error instead of being silently dropped.
            with busy.writing():
                photos_routes.save_manifest(job, manifest)

        from photo_pages import build_photo_docx  # sys.path set up by the photos import above

        template = Path(os.environ.get("RRF_PHOTO_TEMPLATE", DEFAULT_PHOTO_TEMPLATE))
        with busy.writing():
            try:
                out = build_photo_docx(manifest_file, template)
            except Exception as exc:
                raise HTTPException(500, f"Build failed: {exc}")
        return {"created": out.name}

    # Any /api request using a write method (POST/PUT/PATCH/DELETE) that
    # reaches here matched none of the specific routes above -- e.g. a
    # traversal attempt like "/api/jobs/..%2F..%2Fevil/photos", whose
    # decoded "name" contains a "/" and so can never match the
    # single-segment {name} routes. Without this, such a request would
    # fall through to the static mount below, which only serves GET/HEAD
    # and would answer with a misleading 405 instead of a 400/404.
    # Deliberately excludes GET/HEAD: an unmatched GET under /api is left
    # to fall through to the static mount's own ordinary "not found"
    # handling below, unchanged from before this endpoint existed.
    @app.api_route("/api/{_full_path:path}", methods=["POST", "PUT", "PATCH", "DELETE"])
    def api_not_found(_full_path: str):
        raise HTTPException(404, "Not found.")

    # Serve the built front end (app/web/dist, produced by `npm run build`)
    # when it exists. Mounted last, after every /api route above (including
    # the catch-all just above), because StaticFiles(html=True) mounted at
    # "/" swallows any path not claimed by a route registered before it --
    # registering it first would shadow every /api endpoint in this app.
    dist = Path(__file__).resolve().parents[1] / "web" / "dist"
    if dist.is_dir():
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles

        # index.html is never cached. Every build gives the script and stylesheet
        # a new name, so a browser holding an old index.html keeps asking for a
        # file that no longer exists and shows yesterday's app instead. That
        # happened, and it cost a round of testing chasing a defect that was
        # already fixed. The named assets stay cacheable: their names change
        # when their contents do, so they can never go stale.
        # HEAD as well as GET: a HEAD answered by the static mount below would
        # come back without the header, which is exactly what a cache asks
        # when it is deciding whether to reuse what it already has.
        @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
        @app.api_route("/index.html", methods=["GET", "HEAD"], include_in_schema=False)
        def index():
            return FileResponse(dist / "index.html",
                                headers={"Cache-Control": "no-store"})

        app.mount("/", StaticFiles(directory=str(dist), html=True), name="web")

    return app


app = create_app()

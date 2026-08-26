import datetime
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from typing import Optional

from pydantic import BaseModel

import brief
import browse
import busy
import captions
import aipolicy
import classify
import cost
import inventory
import jobfacts
import naming
import pricing
import progress
import reveal
import usage as usage_store
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
    # Set only by the second button on the folder screen, "Use as new jobs
    # folder". It is a deliberate answer to a question the app asked, never a
    # default and never a retry of the same press.
    accept_empty: bool = False


class ActiveJobs(BaseModel):
    active: list[str]


class Classification(BaseModel):
    file: str
    label: str


class FileOnly(BaseModel):
    file: str


class JobFacts(BaseModel):
    city: str = ""
    address: str = ""


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
        # First, before any judgement about the folder. A reset replacing the
        # folders under him is a better answer than "no jobs were found in
        # here", which would be true and useless. Same order as Build.
        busy.check_not_resetting()
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
        # Three places are never the jobs folder, whatever he presses. None of
        # them is a mistake the app can let him make deliberately: the top of a
        # disk and his home folder both hold hundreds of unrelated folders, and
        # a single job folder would make the app list Mark's own eight folders
        # as though each were a job.
        if workspace.is_filesystem_root(Path(path)):
            raise HTTPException(
                400, "That is the top of the disk, not a folder of jobs. Open "
                     "the folder your job folders sit in, then choose it.")
        if workspace.is_home_folder(Path(path)):
            raise HTTPException(
                400, "That is your home folder, which holds everything on this "
                     "computer. Open the folder your job folders sit in, then "
                     "choose it.")
        if workspace.looks_like_job(Path(path)):
            raise HTTPException(
                400, "This looks like one job rather than the folder your "
                     "jobs sit in. Go up one level and choose the folder "
                     "that holds this job.")

        # An empty folder is the one refusal he can answer. Starting a new jobs
        # folder before the first job exists is a real thing to want, and the
        # first version of this check made it impossible. It stays a separate,
        # deliberate press rather than a retry of the same one, so it can never
        # be reached by clicking the same button twice.
        if facts["job_count"] == 0:
            if facts["folder_count"] == 0:
                if not body.accept_empty:
                    raise HTTPException(
                        400, "There is nothing in this folder yet. Choose it as "
                             "a new jobs folder if that is what you want, or go "
                             "up a level and pick the folder your job folders "
                             "sit in.")
            else:
                raise HTTPException(
                    400, "No jobs were found in here. Open the folder your job "
                         "folders sit in, then choose it.")
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
            found = jobs.job_detail(home_or_400(), name)
        except (FileNotFoundError, ValueError):
            raise HTTPException(404, "Job not found.")
        # The number the Photos screen shows, not the number of files in the
        # folder. Two screens quoting two numbers for one section is the app
        # disagreeing with itself in front of him.
        import photos as photos_for_count
        found["photo_count"] = photos_for_count.report_count(
            jobs.resolve_job(home_or_400(), name))
        return found

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
                     "samples": list(s["samples"]),
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

    @app.get("/api/jobs/{name}/photo-groups")
    def photo_groups(name: str):
        """Where this job keeps its photographs, and which set he chose.

        `needs_choice` is the only thing the screen has to act on: more than
        one place holds photographs and he has not said which is the report.
        A job whose photographs all sit in one place never asks.
        """
        job = photos_routes._job_or_404(name)
        groups = photos_routes.photo_groups(job)
        chosen = jobfacts.photo_folder(job)
        here = {g["folder"] for g in groups}
        return {"groups": groups,
                "chosen": chosen,
                "chosen_missing": chosen is not None and chosen not in here,
                "needs_choice": chosen is None and len(groups) > 1}

    class PhotoGroup(BaseModel):
        folder: str

    @app.put("/api/jobs/{name}/photo-group")
    def put_photo_group(name: str, body: PhotoGroup):
        """Record which folder holds the report photographs.

        Refused unless that folder is one the app can see photographs in right
        now, so no answer can be recorded for a place it has not just looked
        at. Nothing is written into his job folder: the answer lives in the
        app's own file, the same as his naming corrections.
        """
        job = photos_routes._job_or_404(name)
        here = {g["folder"] for g in photos_routes.photo_groups(job)}
        if body.folder not in here:
            raise HTTPException(
                400, "There are no photographs in that folder of this job.")
        with busy.writing():
            jobfacts.save_photo_folder(job, body.folder)
        return {"chosen": body.folder}

    @app.put("/api/jobs/{name}/classification")
    def put_classification(name: str, body: Classification):
        job = photos_routes._job_or_404(name)
        # Refused before anything is written, so a claim the app cannot act on
        # never becomes a record that does nothing.
        said = classify.refusal(job, body.file, body.label)
        if said:
            raise HTTPException(400, said)
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

    def _uncaptioned(job: Path, manifest: dict) -> list:
        """The included photographs still waiting for words, as real paths.

        Never trusts a filename string from the manifest: each one is resolved
        and confirmed to sit inside this job's Photos folder before it can be
        opened, using photos.py's own confinement helper rather than a
        parallel path check. A photo that already has a caption is not here,
        which is what makes a retry send only what is left and never pay for
        the same picture twice.
        """
        photos_dir = jobs.photos_dir(job)
        waiting = []
        for entry in photos_routes.included(manifest):
            if str(entry.get("caption", "")).strip():
                continue
            candidate = photos_dir / Path(entry["file"]).name
            resolved = photos_routes._resolve_confined(candidate, photos_dir)
            if resolved is not None and resolved.is_file():
                waiting.append(resolved)
        return waiting

    def _image_settings_version() -> str:
        from photo_prep import SETTINGS_VERSION
        return SETTINGS_VERSION

    def _bucket() -> str:
        return cost.bucket_name(captions.MODEL, _image_settings_version())

    @app.get("/api/jobs/{name}/caption-estimate")
    def caption_estimate(name: str):
        """What a run would send and what it would cost, before he asks for it.

        Reports the ceiling and the refusal without touching the network, so
        the screen can show the number and the block for free.
        """
        job = photos_routes._job_or_404(name)
        manifest = photos_routes.load_manifest(job)
        waiting = _uncaptioned(job, manifest)
        allowed = aipolicy.classify_job(job)
        tranches = captions.plan_tranches(waiting) if waiting else []
        blocked = (aipolicy.LOCAL_ONLY if allowed == aipolicy.LOCAL_ONLY
                   else "no_key" if not captions.ai_available()
                   else "nothing_to_do" if not waiting
                   else "")
        return {
            "photos_to_send": len(waiting),
            "tranches": len(tranches),
            "tranche_size": captions.MAX_PER_TRANCHE,
            "needs_confirmation": len(waiting) > captions.CONFIRM_ABOVE,
            "confirm_above": captions.CONFIRM_ABOVE,
            "estimate": cost.estimate(len(waiting), _bucket()),
            "ai_available": captions.ai_available(),
            "policy": allowed,
            "may_send": allowed != aipolicy.LOCAL_ONLY,
            # One reason, so no control is ever grey without saying why.
            "blocked_because": blocked,
            "review": photos_routes.review_progress(manifest),
        }

    @app.post("/api/jobs/{name}/captions")
    def draft_job_captions(name: str, confirmed: bool = False):
        """Caption every included photograph that has none, and stop there.

        The order below is the safety. Nothing reaches the network until the
        policy has allowed it, the ceiling has been checked, and the count is
        known, and every batch that succeeds is written to disk before the
        next one is sent.
        """
        job = photos_routes._job_or_404(name)
        manifest = photos_routes.load_manifest(job)

        # 1. May this job's photographs leave the machine at all? Asked before
        #    a client is constructed, so a refusal costs nothing.
        try:
            verdict = aipolicy.classify_job(job)
        except state.StateUnreadable:
            raise HTTPException(409, aipolicy.UNREADABLE_MESSAGE)
        if verdict == aipolicy.LOCAL_ONLY:
            raise HTTPException(403, aipolicy.LOCAL_ONLY_MESSAGE)

        if not captions.ai_available():
            return {**manifest, "ai_available": False}

        waiting = _uncaptioned(job, manifest)
        if not waiting:
            return {**manifest, "ai_available": True,
                    "review": photos_routes.review_progress(manifest)}

        # 2. Above thirty, he has to have said yes. There is no ceiling: the
        #    confirmation informs, it does not refuse, and the screen sends
        #    confirmed=true once he has seen the number.
        if len(waiting) > captions.CONFIRM_ABOVE and not confirmed:
            raise HTTPException(
                409, "This run needs confirming first. %d photos will be sent."
                     % len(waiting))

        shown = cost.estimate(len(waiting), _bucket())
        tranches = captions.plan_tranches(waiting)

        done, usages, failure = 0, [], None
        progress.start(name, len(waiting), len(tranches))
        try:
            for tranche_number, batch in enumerate(tranches, start=1):
                try:
                    drafted, used = captions.draft_captions(
                        manifest.get("context", ""), batch,
                        style=manifest.get("caption_style", captions.DEFAULT_STYLE))
                except captions.CaptionError as exc:
                    # 3. Everything already paid for stays. Only the batch that
                    #    failed and the ones never sent are left without words.
                    failure = exc
                    break

                usages.append(used)
                # 4. Saved immediately, as unreviewed drafts, before the next
                #    request goes out. A refresh, a crash or a later failure
                #    cannot lose work that has already been charged for.
                with busy.writing():
                    for entry in photos_routes.included(manifest):
                        if not str(entry.get("caption", "")).strip():
                            fresh = drafted.get(entry["file"], "")
                            if fresh:
                                entry["caption"] = fresh
                                entry.pop(photos_routes.REVIEWED, None)
                                done += 1
                    photos_routes.save_manifest(job, manifest)
                # Written after the save, never before it, so the number the
                # screen shows is a number of captions already on disk.
                progress.advance(name, tranche_number, done)
        finally:
            # However this ends, including a way nobody predicted. A progress
            # light stuck on would leave the screen polling for ever.
            progress.finish(name)
        measured = cost.measured(captions.MODEL, usages)
        remaining = [p.name for p in _uncaptioned(job, photos_routes.load_manifest(job))]

        # 5. Recorded whatever happened, so the estimate can learn and so the
        #    run can be audited later. Counts, tokens and rates only.
        try:
            usage_store.open_bucket(_bucket())
            usage_store.record_run({
                "run_id": "%s-%d" % (_bucket().split("/")[0], len(usage_store.runs()) + 1),
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                "model": captions.MODEL,
                "pricing_version": measured["pricing_version"],
                "pricing_rates": pricing.rates_for(captions.MODEL) or {},
                "image_settings_version": _image_settings_version(),
                "photos_requested": len(waiting),
                "photos_captioned": done,
                "photos_remaining": len(remaining),
                "api_requests": len(usages),
                "status": ("completed" if failure is None and not remaining else
                           "failed" if done == 0 else "partial")
                          if measured["calculated_cost"] is not None
                          else usage_store.COST_UNAVAILABLE,
                "estimate": shown["total"],
                "token_usage": usages,
                "calculated_cost": measured["calculated_cost"],
                # The rate *after* this run, which means this run's own cost
                # and photographs have to be counted in. Reading the stored
                # runs here would give the rate before it, because the record
                # being built is not saved yet.
                "learned_rate": round(cost.rate_including(
                    _bucket(), measured["calculated_cost"], done), 6),
            })
        except Exception:
            # Bookkeeping must never take the run down or lose paid captions.
            pass

        fresh_manifest = photos_routes.load_manifest(job)
        answer = {**fresh_manifest, "ai_available": True,
                  "estimate_shown": shown,
                  "measured": measured,
                  "captioned": done,
                  "remaining": remaining,
                  "requested": len(waiting),
                  "tranches_planned": len(tranches),
                  "tranches_done": len(usages),
                  "review": photos_routes.review_progress(fresh_manifest)}
        # What actually happened to the run, in one word and one sentence, said
        # here because only the run knows. A single request cannot: it failed,
        # and whether that leaves nothing saved or sixty captions saved depends
        # on the requests before it. The screen used to put the request's own
        # sentence, "Nothing was changed", directly under a box reporting sixty
        # saved captions.
        answer["state"] = ("done" if failure is None and not remaining else
                           "partial" if done > 0 else "failed")
        if answer["state"] == "partial":
            answer["summary"] = (
                "%d %s saved. %d %s still %s a caption. The captions already "
                "saved will not be sent or charged for again."
                % (done, "caption was" if done == 1 else "captions were",
                   len(remaining), "photo" if len(remaining) == 1 else "photos",
                   "needs" if len(remaining) == 1 else "need"))
        elif answer["state"] == "done":
            answer["summary"] = ("%d %s written."
                                 % (done, "caption was" if done == 1 else "captions were"))
        else:
            answer["summary"] = "No captions were written. Nothing was changed."

        if failure is not None:
            answer["error"] = failure.message
            answer["error_kind"] = failure.kind
            answer["partial"] = done > 0
        return answer

    @app.get("/api/jobs/{name}/caption-progress")
    def caption_progress(name: str):
        """How far a running caption run has got. Asked on a timer.

        Deliberately not authoritative about captions: the manifest is. This
        says which request the run is on and how many captions are already
        saved, so the screen can show a position instead of a bar that only
        proves something is happening.
        """
        photos_routes._job_or_404(name)
        return progress.read(name)

    @app.get("/api/jobs/{name}/facts")
    def job_facts(name: str):
        """The city and address Build will use, and where they came from.

        Shown near the Build action so a wrong split is visible before it
        reaches a filename rather than afterwards.
        """
        job = photos_routes._job_or_404(name)
        found = naming.facts_for(job)
        try:
            found["filename"] = naming.output_base(found["city"], found["address"]) + ".docx"
        except ValueError:
            found["filename"] = ""
        return found

    @app.put("/api/jobs/{name}/facts")
    def correct_job_facts(name: str, body: JobFacts):
        """His correction, stored app-side and never in his job folder."""
        job = photos_routes._job_or_404(name)
        with busy.writing():
            jobfacts.save(job, body.city, body.address)
        return job_facts(name)

    @app.post("/api/jobs/{name}/build")
    def build_photos(name: str):
        # First, before any validation. A reset replacing the folders under
        # him is a better answer than "your captions need review".
        busy.check_not_resetting()
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

        # A photograph named in the manifest file that is not in the folder
        # used to surface as the engine's own exception, because the engine
        # read that file directly. It no longer does: Mark chooses which
        # folder holds the report photographs, so the engine is handed the
        # list instead. That made a dangling entry disappear silently, which
        # is worse than the crash it replaced, so the check is now explicit
        # and it runs whether or not he has chosen anything.
        if manifest_existed:
            try:
                raw = json.loads(manifest_file.read_text())
            except ValueError:
                raw = {}
            if isinstance(raw, dict):
                for entry in raw.get("photos", []) or []:
                    if not isinstance(entry, dict) or entry.get("cut"):
                        continue
                    named = entry.get("file")
                    if not named:
                        continue
                    where = jobs.photo_path(job, entry)
                    if not where.is_file():
                        raise HTTPException(
                            500, "Build failed: %s is named in "
                                 "photo-manifest.json but is not in the Photos "
                                 "folder." % named)

        # Every included caption has to have been looked at. This is the gate,
        # and it is here rather than only on the screen because the manifest is
        # hand-editable and the screen is courtesy.
        progress = photos_routes.review_progress(manifest)
        if not progress["all_reviewed"]:
            raise HTTPException(
                400, "%s. Tick every photo you have read before building."
                     % progress["text"])

        # The name comes from the brief or from his correction, and never from
        # the folder. Refusing costs ten seconds; a confidently wrong filename
        # reaches a client.
        found = naming.facts_for(job)
        if not found["ready"]:
            missing = found["missing"]
            raise HTTPException(
                400, "The %s %s missing, so the file cannot be named. Enter %s "
                     "next to Build and try again."
                     % (" and ".join(missing),
                        "is" if len(missing) == 1 else "are",
                        "it" if len(missing) == 1 else "them"))
        out_base = naming.output_base(found["city"], found["address"])

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
        from photo_prep import Workspace

        with busy.writing():
            # The copies live in the workspace and go with it, on the way out
            # of the try and on the way out of an exception alike. The
            # originals are only ever read.
            with Workspace() as bench:
                try:
                    # The list, not the file. Mark chooses which folder
                    # inside Photos holds the report photographs and the file
                    # deliberately still holds all of them with their captions,
                    # so the engine reading it would put photographs in the
                    # document that he did not choose. This list is the same
                    # one the gate above already refused to build without.
                    out = build_photo_docx(manifest_file, template,
                                           prepare=bench.copy_for_document,
                                           out_base=out_base,
                                           entries=photos_routes.included(manifest))
                except Exception as exc:
                    raise HTTPException(500, f"Build failed: {exc}")
        # The folder is named as well as the file, so the screen can offer to
        # open either without deriving a path of its own.
        return {"created": out.name, "folder": str(out.parent)}

    class RevealWhat(BaseModel):
        file: str
        # "document" opens it, "folder" shows it in the folder it was saved in.
        what: str = "document"

    @app.post("/api/jobs/{name}/reveal")
    def reveal_built_file(name: str, body: RevealWhat):
        """Open a built document, or show it in its folder. Never on its own.

        Confined the same way every other file route is: a bare name, resolved,
        and required to land inside this job's own Photos folder. Without that,
        this would open any file on the machine that could be named.
        """
        job = photos_routes._job_or_404(name)
        photos_dir = jobs.photos_dir(job)
        candidate = photos_dir / Path(body.file).name
        target = photos_routes._resolve_confined(candidate, photos_dir)
        if target is None or not target.is_file():
            raise HTTPException(404, "That file is not in this job's Photos folder.")
        try:
            if body.what == "folder":
                reveal.show_in_folder(target)
            else:
                reveal.open_document(target)
        except reveal.RevealFailed as exc:
            # 409, not 500. Nothing is broken: the document is written and
            # verified, and only the handing-over failed. The body carries the
            # saved path so the screen can show him where it is.
            raise HTTPException(409, "%s Saved at: %s" % (exc.message, target))
        return {"opened": target.name, "folder": str(target.parent)}

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

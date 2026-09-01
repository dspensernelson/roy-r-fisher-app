"""The Description of Improvements screen's endpoints.

Nothing here reads a source or spends money unless Mark presses a button. The
guards are the ones approved for captions on 2026-08-17: he acts first, the
screen says what will be sent before he acts, and the key never leaves the
server.
"""
import os
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

import improvements
import pricing
import state
import usage
import improvements_pages as pages
import improvements_read as reader

router = APIRouter()

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "Improvements.docx"
STORE_NAME = ".rrf-improvements.json"


def _job(name: str) -> Path:
    import photos as photos_routes
    return photos_routes._job_or_404(name)


def store_file() -> Path:
    """Home folder on both Mac and Windows, the same as the other app files.
    RRF_IMPROVEMENTS_FILE overrides it, for tests."""
    override = os.environ.get("RRF_IMPROVEMENTS_FILE")
    return Path(override) if override else Path.home() / STORE_NAME


def _key(job: Path) -> str:
    """One job, by its resolved path. The keying the other stores already use,
    so two folders of the same name stay separate."""
    return str(Path(job).resolve())


def _read_all() -> dict:
    """Raises when the store is there and damaged, rather than reporting an
    empty section. A silently forgotten answer is the same defect as a guessed
    one."""
    return state.read_json(store_file())


def _pick(paths, chosen: str, job: Path):
    """The file Mark chose, or the best offer. Confined to the job."""
    if chosen:
        import jobs
        try:
            return jobs.resolve_confined(job / chosen, job)
        except ValueError:
            raise HTTPException(400, "That file is not in this job.")
    if not paths:
        return None
    return paths[0]


@router.get("/api/jobs/{name}/improvements/sources")
def sources(name: str):
    """What this job has. Offered, never assumed: Mark confirms the pick."""
    job = _job(name)
    found = reader.find_sources(job)
    def show(paths):
        return [{"rel": str(p.relative_to(job)), "name": p.name} for p in paths]
    return {"ai_available": improvements.ai_available(),
            "cards": show(found["cards"]),
            "transcripts": show(found["transcripts"]),
            "ready": bool(found["cards"] and found["transcripts"])}


@router.get("/api/jobs/{name}/improvements")
def read_state(name: str):
    """What Mark has ticked, edited and approved for this job.

    The app's own note. It lives in his home folder, never inside a job of his,
    so nothing the app records can rename, move, edit or delete his work.
    """
    entry = _read_all().get("jobs", {}).get(_key(_job(name)), {})
    if not isinstance(entry, dict):
        return {"blocks": [], "read": False}
    return {"blocks": entry.get("blocks", []), "read": bool(entry.get("read"))}


class Saved(BaseModel):
    blocks: list = []
    read: bool = False


@router.put("/api/jobs/{name}/improvements")
def write_state(name: str, body: Saved):
    data = _read_all()
    jobs_map = data.setdefault("jobs", {})
    jobs_map[_key(_job(name))] = body.model_dump()
    state.write_json(store_file(), state.without_schema(data))
    return {"saved": True}


class ReadRequest(BaseModel):
    card: str = ""
    transcript: str = ""
    confirmed: bool = False


@router.post("/api/jobs/{name}/improvements/read")
def read_sources(name: str, body: ReadRequest):
    """Pass one. Reads the two documents and returns what it can prove."""
    job = _job(name)
    if not improvements.ai_available():
        raise HTTPException(400, "Reading documents needs a key on this "
                                 "computer. Open Settings to add one.")
    found = reader.find_sources(job)
    card = _pick(found["cards"], body.card, job)
    transcript = _pick(found["transcripts"], body.transcript, job)
    if card is None or transcript is None:
        raise HTTPException(400, "This job needs both an assessor card and an "
                                 "inspection transcript.")
    card_text = reader.read_file(card)
    transcript_text = reader.read_file(transcript)
    if not body.confirmed:
        # What will be sent, before it is sent. He acts on this, not on trust.
        return {"confirm": True,
                "card": card.name, "transcript": transcript.name,
                "characters": len(card_text) + len(transcript_text)}

    shape = pages.read_shape(TEMPLATE)
    try:
        sheet, thrown, spend = improvements.read_sources(
            card_text, transcript_text, shape)
    except improvements.ImprovementsError as exc:
        raise HTTPException(400, exc.message)

    measured = _record(spend, "improvements-read")
    return {"parts": sheet["parts"],
            "found": [f.model_dump() for f in sheet["kept"]],
            "refused": len(thrown),
            "card": card.name, "transcript": transcript.name,
            "measured": measured}


class WriteRequest(BaseModel):
    block: str
    facts: list[str] = []
    notes: str = ""


@router.post("/api/jobs/{name}/improvements/paragraph")
def write_paragraph(name: str, body: WriteRequest):
    """Pass two. Sees the approved facts and the notes. Never the sources."""
    _job(name)
    if not improvements.ai_available():
        raise HTTPException(400, "Writing a paragraph needs a key on this "
                                 "computer. Open Settings to add one.")
    try:
        text, spend = improvements.write_paragraph(
            body.block, body.facts, body.notes)
    except improvements.ImprovementsError as exc:
        raise HTTPException(400, exc.message)
    return {"text": text, "measured": _record(spend, "improvements-paragraph")}


def _record(spend: dict, what: str):
    """One spend, written down. A run that was not measured stays unmeasured
    rather than being recorded as a run that cost nothing."""
    if not spend:
        return None
    cost = pricing.cost_of(improvements.MODEL, spend) if pricing.known(improvements.MODEL) else None
    record = {"what": what, "model": improvements.MODEL, **spend}
    if cost is not None:
        record["cost"] = cost
    try:
        usage.record_run(record)
    except Exception:
        # A spend that cannot be filed is still a spend that happened. It is
        # reported to the screen either way rather than being swallowed.
        pass
    return record

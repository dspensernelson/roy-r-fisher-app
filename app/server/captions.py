"""Draft photo captions in one of the firm's two measured styles.

Measured across the corpus 2026-08-10. Twelve photo documents; five carry real
captions. Four of them, 79 captions between them, write "View of <what> facing
<direction>". The fifth, 24 captions, writes a category, a dash, and a detail,
and it is the only multi-family building among them.

Which delivered reports those were is recorded in the development notes, not
here. This file ships to Mark, and a client's town and tenant have no business
travelling inside it just to explain where a default came from.

So "View of" is the house default and the category form is offered where the
property type suggests it. The category form rests on ONE delivered report and
is flagged as such wherever Mark sees it, the same way the section picker
flags a thin engagement column.

Mark's pick always outranks the property type. This module only proposes.
"""
import base64
import io
import os
from pathlib import Path

from PIL import Image
from pydantic import BaseModel

MODEL = "claude-opus-5"

_SHARED_RULES = """
- Describe only what is visible. Never state a measurement, a count, a material, an address, or a tenant name you cannot see in the photo.
- A compass direction is not visible in a photograph. Never state one unless the photo itself proves it, for example a sign reading "North Entrance". Leave the direction out and let the appraiser add it. He was standing there; you were not. Getting a direction wrong in a delivered report is worse than leaving it blank.
- No numbering. No "Photo of" or "Image of". No trailing period.
- Keep it to one line, roughly four to twelve words.
- If a photo is unclear or you cannot tell what it shows, return an empty caption rather than guessing. The appraiser will fill it in."""

STYLES = {
    "view": {
        "label": "View of",
        "sample": "View of northwest corner facing southeast",
        # Shown on the style step, which now sends nothing and calls nobody.
        # Invented for the screen on purpose: generic building parts, no
        # client, no address, no tenant, and deliberately not captions of the
        # photographs he has open. Pairing a written line with one of his
        # photographs would be a claim about that photograph that the app
        # cannot observe, which is the one thing this app must never do.
        "samples": [
            "View of the front entrance",
            "View of the main office",
            "View of the parking area",
        ],
        "note": "Measured across four delivered reports, 79 captions.",
        "thin_evidence": False,
        "prompt": """Write each caption as a view statement, the firm's most common form.

Real captions from delivered reports:

  View of northwest corner facing southeast
  View of northeast corner facing southwest
  View of west entrance, grocery side
  View of building's west side, dock doors(4)
  View of exterior from southwest facing east along south wall
  View of auto center from the south facing northwest, building's east wall
  View of main office at front entrance
  View of Conference/Training Room

Rules:
- Open with "View of". Where the subject is equipment rather than a place, "View" alone is also used ("View transformer along exterior south wall").
- The delivered captions above name compass directions because the appraiser was on site and knew them. You are not, so do not guess one. Describe what the photo shows and let him add the direction.
- Name a room or a functional area directly when the photo is interior ("View of Conference/Training Room").
- Never use a dash to split the caption into a category and a detail. That is the other style.""",
    },
    "category": {
        "label": "Location first",
        "sample": "Building exterior – northwest corner facing southeast",
        # The same three subjects as the other style, so the step shows one
        # difference and not two: the form changes, the subjects do not.
        "samples": [
            "Building exterior – front entrance",
            "Common area – main office",
            "Site – parking area",
        ],
        "note": "Rests on ONE delivered report, a multi-family building, 24 captions.",
        "thin_evidence": True,
        "prompt": """Write each caption as a category, an en dash, then the specific detail.

Real captions from the one delivered report that uses this form:

  Building exterior – front signage facing southwest from parking lot
  Building exterior – front entrance
  Building exterior – rear/east side of building
  Building exterior – dumpster along west side of parking lot
  Common Area – front entry
  Common Area – office and mailboxes and hallway
  Common Area – laundry facilities
  Common Area – furnace room
  Typical kitchen – unit 2
  Bathroom – unit 1

Rules:
- Lead with the category the photo belongs to. Use the firm's own vocabulary where it fits: "Building exterior", "Common Area", "Typical <room>", "<Room> – unit N". Coin a new category only when none of these fit.
- The delivered captions above name compass directions because the appraiser was on site and knew them. You are not, so do not guess one.
- This form was measured on a residential building, so its vocabulary is rooms and units. Adapt the category to what the property actually is.""",
    },
}

DEFAULT_STYLE = "view"

# The one delivered report using the category form is multi-family, so that is
# where the app suggests it. Everything else starts on the house default.
CATEGORY_PROPERTY_TYPES = ("multi-family", "multifamily", "multi family",
                           "apartment", "residential")


class PhotoCaption(BaseModel):
    filename: str
    caption: str


class CaptionSheet(BaseModel):
    captions: list[PhotoCaption]


def ai_available() -> bool:
    """Whether captions can be written on this computer.

    Asks settings for the key rather than reading the environment itself, so
    a key that lives only in the file counts. It used to check the
    environment alone, which meant the answer depended on whether the app had
    been started by the launcher.
    """
    import settings
    return bool(settings.active_key())


def default_style(property_type: str) -> str:
    """The style to start a job on, from its property type. A suggestion only."""
    text = (property_type or "").strip().lower()
    if any(word in text for word in CATEGORY_PROPERTY_TYPES):
        return "category"
    return DEFAULT_STYLE


def system_prompt(style: str) -> str:
    """The instructions for one style. An unknown style falls back to the
    house default rather than raising, because this sits behind a stored
    manifest value that a human can edit by hand."""
    chosen = STYLES.get(style) or STYLES[DEFAULT_STYLE]
    return (
        "You are captioning subject photographs for a Roy R. Fisher commercial "
        "appraisal report. Write one caption per photo, in the firm's house style.\n\n"
        f"{chosen['prompt']}\n{_SHARED_RULES}"
    )


def _thumb_b64(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode()


# The largest number of photographs in one provider request. Corrected
# 2026-08-20: this used to be a ceiling on the whole run, and a job holding 61
# photographs simply could not be captioned, which made the app useless for
# exactly the jobs that need it most. It is now the size of a tranche and
# nothing more. A run of any size is divided into tranches of at most this
# many, automatically, and Mark never has to know.
MAX_PER_TRANCHE = 60

# Above this many unfinished photographs the screen asks him to confirm the
# spend before anything is sent. It informs; it never refuses.
CONFIRM_ABOVE = 30

# How much encoded image one request may carry. Sixty thumbnails do not fit in
# a single request at any realistic size, so a full run always splits. This is
# deliberately well under the provider's own limit: the cost of one extra
# request is small and the cost of a rejected oversized one is a whole run.
# RRF_MAX_REQUEST_BYTES lowers it, so a split can be forced on a handful of
# photographs during calibration instead of having to send sixty to see one.
# The same shape of override the state paths already use, and for the same
# reason: proving a behaviour should not require staging the expensive
# conditions that normally produce it.
MAX_REQUEST_BYTES = int(os.environ.get("RRF_MAX_REQUEST_BYTES") or (12 * 1024 * 1024))

# Retries are off. A failed request shows Mark a clear error and waits for him
# to ask again, because an automatic retry spends money he has not agreed to
# spend and can do it while he is looking at an error message.
MAX_RETRIES = 0


class CaptionError(Exception):
    """A caption run failed, already worded the way Mark should read it."""

    def __init__(self, message: str, kind: str = "failed"):
        super().__init__(message)
        self.message = message
        self.kind = kind


def plan_tranches(photo_paths: list, encoded: dict = None) -> list:
    """Divide the run into requests: at most sixty each, smaller if size forces it.

    Two limits, and they are different kinds of thing. Sixty is the provider's
    practical comfort for one request and is the one Mark would otherwise have
    met as a wall. The byte limit is about what actually fits on the wire, and
    a tranche is cut short when the encoded images reach it.

    The whole run always goes somewhere: 61 becomes 60 + 1, 100 becomes
    60 + 40, 121 becomes 60 + 60 + 1. Nothing is refused for being large.
    """
    tranches, current, running = [], [], 0
    for path in photo_paths:
        size = len((encoded or {}).get(str(path), "")) or _encoded_size(path)
        too_many = len(current) >= MAX_PER_TRANCHE
        too_big = current and running + size > MAX_REQUEST_BYTES
        if too_many or too_big:
            tranches.append(current)
            current, running = [], 0
        current.append(path)
        running += size
    if current:
        tranches.append(current)
    return tranches


def _encoded_size(path) -> int:
    try:
        return len(_thumb_b64(Path(path)))
    except Exception:
        # Unreadable here is not fatal: the request itself will fail and say
        # so. Assume a large one so a bad file cannot silently overfill a batch.
        return MAX_REQUEST_BYTES // 4


def _usage_of(response) -> dict:
    """What the provider said this request used, as plain numbers.

    Missing counters stay missing rather than becoming zero, because the cost
    ledger has to be able to tell "no cache was read" from "we were not told".
    """
    found = getattr(response, "usage", None)
    if found is None:
        return {}
    def number(*names):
        for name in names:
            value = getattr(found, name, None)
            if value is not None:
                return int(value)
        return None
    return {"input": number("input_tokens"),
            "output": number("output_tokens"),
            "cache_write": number("cache_creation_input_tokens") or 0,
            "cache_read": number("cache_read_input_tokens") or 0}


def draft_captions(context: str, photo_paths: list,
                   style: str = DEFAULT_STYLE) -> tuple:
    """Caption one batch. Returns (captions by filename, usage for this request).

    One request. Dividing a run across requests is `plan_tranches` and the caller's
    loop, so that a failure part way through a split run loses only the batch
    that failed and never the ones already paid for.
    """
    import anthropic
    import settings

    # Handed the key explicitly. Left to itself the client reads the
    # environment, which would work only when something outside the program
    # had put the key there. The key goes no further than this call: it is
    # never printed, logged, returned or written into a job.
    client = anthropic.Anthropic(api_key=settings.active_key(),
                                 max_retries=MAX_RETRIES)
    content = [{"type": "text", "text": f"Job context: {context or 'not provided'}. Caption each photo."}]
    for p in photo_paths:
        content.append({"type": "text", "text": f"Photo filename: {p.name}"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": _thumb_b64(p)}})

    try:
        response = client.messages.parse(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt(style),
            messages=[{"role": "user", "content": content}],
            output_format=CaptionSheet,
        )
    except anthropic.AuthenticationError:
        raise CaptionError("That API key was not accepted. Open Settings and "
                           "paste it again.", "bad_key")
    except anthropic.PermissionDeniedError:
        raise CaptionError("That API key does not have access to write "
                           "captions. Contact Spenser.", "no_access")
    except anthropic.RateLimitError:
        # Deliberately no longer claims that nothing was changed. A run is
        # divided into requests and every finished one is saved before the
        # next is sent, so this can be raised with sixty captions already on
        # disk. The screen showed this sentence directly under a box reporting
        # those sixty, and the two contradicted each other. What did or did not
        # survive is a fact about the run, not about one request, and the run
        # says it now.
        raise CaptionError("Anthropic is busy or the account has hit a limit. "
                           "Try again in a minute.", "rate")
    except anthropic.APIStatusError as exc:
        status = getattr(exc, "status_code", None)
        if status in (400, 413):
            raise CaptionError("That request was too large to send. Cut some "
                               "photos and try again.", "too_large")
        raise CaptionError("Anthropic refused the request. This can mean the "
                           "spending limit has been reached. Contact Spenser.",
                           "refused")
    except anthropic.APIConnectionError:
        raise CaptionError("Could not reach Anthropic. Check the internet "
                           "connection and try again. Nothing was sent twice.",
                           "unreachable")

    sheet = response.parsed_output
    captions = {c.filename: c.caption for c in sheet.captions} if sheet else {}
    return captions, _usage_of(response)

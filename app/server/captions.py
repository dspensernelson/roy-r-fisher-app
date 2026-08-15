"""Draft photo captions in one of the firm's two measured styles.

Measured across the corpus 2026-08-10. Twelve photo documents; five carry real
captions. Four of them (79 captions: Mason City Walmart, both Burlington
documents, and one old report) write "View of <what> facing <direction>". The
fifth (24 captions, 215 E 37th Street) writes a category, a dash, and a
detail, and it is the only multi-family building among them.

So "View of" is the house default and the category form is offered where the
property type suggests it. The category form rests on ONE delivered report and
is flagged as such wherever the appraiser sees it, the same way the section picker
flags a thin engagement column.

The appraiser's pick always outranks the property type. This module only proposes.
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


def draft_captions(context: str, photo_paths: list[Path],
                   style: str = DEFAULT_STYLE) -> dict[str, str]:
    import anthropic
    import settings

    # Handed the key explicitly. Left to itself the client reads the
    # environment, which would work only when something outside the program
    # had put the key there. The key goes no further than this call: it is
    # never printed, logged, returned or written into a job.
    client = anthropic.Anthropic(api_key=settings.active_key())
    content = [{"type": "text", "text": f"Job context: {context or 'not provided'}. Caption each photo."}]
    for p in photo_paths:
        content.append({"type": "text", "text": f"Photo filename: {p.name}"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": _thumb_b64(p)}})
    response = client.messages.parse(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt(style),
        messages=[{"role": "user", "content": content}],
        output_format=CaptionSheet,
    )
    sheet = response.parsed_output
    return {c.filename: c.caption for c in sheet.captions} if sheet else {}

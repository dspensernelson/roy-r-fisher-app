"""Read a job's assessor card and inspection transcript into section fields.

Two model calls, and they are deliberately different in what they may see.

  Pass one reads the two sources and returns a value for each field TOGETHER
  WITH THE WORDS IT TOOK IT FROM. A plain function then checks those words are
  really in that source. Anything that fails is thrown away and the field is
  left empty. That check is `verify` below; it needs no model and it is what
  stops the app stating a fact it cannot point at.

  Pass two writes the GENERAL and CONCLUSION paragraphs. It is handed ONLY the
  values Mark has already approved and the notes he typed. It never sees the
  card or the transcript. So it cannot introduce a fact nobody approved, and
  its prose is checkable by reading the facts above it.

Approved by Spenser 2026-09-01. Measured on the Blaul Lofts job 2026-08-28:
of 21 fields, the transcript alone supplies 9, the two together 3, the card
alone 1, and 4 have no source at all and stay empty.
"""
import os

from pydantic import BaseModel

MODEL = "claude-opus-5"

# One request each way. Mark's card runs to about fourteen thousand characters
# and his transcript about the same, so both fit comfortably.
MAX_TOKENS = 8192
MAX_RETRIES = 0
MAX_SOURCE_CHARS = int(os.environ.get("RRF_MAX_SOURCE_CHARS") or 120_000)


class Found(BaseModel):
    block: str
    part: str
    field: str
    value: str
    source: str
    quote: str


class Sheet(BaseModel):
    parts: list[str]
    found: list[Found]


class Paragraph(BaseModel):
    text: str


class ImprovementsError(Exception):
    def __init__(self, message, kind="failed"):
        super().__init__(message)
        self.message, self.kind = message, kind


READ_RULES = """You are reading two documents about ONE building for a commercial appraiser.

  CARD is the county assessor's property record card.
  TRANSCRIPT is a recording of the appraiser walking the building.

Return a value for a field only when one of those two documents supports it.

THE RULE THAT MATTERS: every value you return carries `quote`, a run of words
copied EXACTLY from the document named in `source`. Copy it character for
character from the document. Do not tidy it, do not correct its spelling, do
not join two separate places together. A value whose quote is not found in that
document is thrown away and the appraiser gets an empty field instead.

An empty field costs him ten seconds. A wrong one reaches his client over his
signature. When in doubt, leave the field out.

Never state a measurement, a material, an age, a count or a condition that is
not in one of the two documents. Never carry anything over from another
building. Never infer: if the card says the walls are brick and the transcript
does not mention walls, that is one source, not two.

Write the `value` in the appraiser's register: a short statement, no lead-in,
no "the transcript says". Sentence case, ending with a full stop.

Return each field once per source that supports it. If both support it, return
two entries and let him see they agree.

`parts` lists the parts of the building that are described separately, in the
order he walked them, for example Common Areas, Commercial Suite, Apartment
Units. On a property with several buildings these are the buildings instead.
Base this on the transcript. Leave it empty if the building is one space.

For a field inside a part, set `part` to that part's name. Otherwise `part` is
an empty string.

You will be told which blocks and fields exist. Use those names exactly."""

WRITE_RULES = """You are writing one paragraph of a commercial appraisal for the appraiser who
signs it.

You are given facts he has already checked and approved, and notes he typed
himself. THAT IS EVERYTHING YOU MAY USE. You have not been shown the assessor
card or the inspection transcript, and you may not reach for anything you think
you know about this building or buildings like it.

Do not add a fact. Do not add a judgement. Do not estimate an age, a condition,
a quality or a remaining life: those are his opinion and he writes them.

Join the facts into plain connected prose in his register. Two to four
sentences. No heading, no bullet points, no lead-in. Say nothing you were not
given."""


def ai_available() -> bool:
    import settings
    return bool(settings.active_key())


def flatten(text: str) -> str:
    from engine.improvements_read import flatten as _f
    return _f(text)


def verify(found, sources: dict):
    """Split what came back into what is provable and what is not.

    Pure. No model, no network, no files. The one function that decides whether
    a value is allowed to reach Mark's report, so it is tested on its own.
    """
    flat = {name: flatten(text) for name, text in sources.items()}
    kept, thrown = [], []
    for item in found:
        body = flat.get(item.source if hasattr(item, "source") else item["source"], "")
        quote = item.quote if hasattr(item, "quote") else item["quote"]
        chunk = flatten(quote)
        (kept if chunk and chunk in body else thrown).append(item)
    return kept, thrown


def _client():
    import anthropic
    import settings
    # Handed the key explicitly. Left to itself the client reads the
    # environment, which would work only when something outside the program had
    # put the key there. The key goes no further than this call: never printed,
    # never logged, never returned, never written into a job.
    return anthropic.Anthropic(api_key=settings.active_key(), max_retries=MAX_RETRIES)


def _call(system, user, shape):
    import anthropic
    try:
        response = _client().messages.parse(
            model=MODEL, max_tokens=MAX_TOKENS, system=system,
            messages=[{"role": "user", "content": user}], output_format=shape)
    except anthropic.AuthenticationError:
        raise ImprovementsError("That API key was not accepted. Open Settings "
                                "and paste it again.", "bad_key")
    except anthropic.PermissionDeniedError:
        raise ImprovementsError("That API key does not have access. Contact "
                                "Spenser.", "no_access")
    except anthropic.RateLimitError:
        raise ImprovementsError("Anthropic is busy or the account has hit a "
                                "limit. Try again in a minute.", "rate")
    except anthropic.APIStatusError as exc:
        if getattr(exc, "status_code", None) in (400, 413):
            raise ImprovementsError("Those documents were too large to send. "
                                    "Contact Spenser.", "too_large")
        raise ImprovementsError("Anthropic refused the request. This can mean "
                                "the spending limit has been reached. Contact "
                                "Spenser.", "refused")
    except anthropic.APIConnectionError:
        raise ImprovementsError("Could not reach Anthropic. Check the internet "
                                "connection and try again.", "unreachable")
    return response


def _usage_of(response):
    """Missing counters stay missing rather than becoming zero, so a spend
    that was not measured never reads as a spend of nothing."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    out = {}
    for name in ("input_tokens", "output_tokens",
                 "cache_creation_input_tokens", "cache_read_input_tokens"):
        value = getattr(usage, name, None)
        if value is not None:
            out[name] = value
    return out


def read_sources(card_text: str, transcript_text: str, shape) -> tuple:
    """Pass one. Returns (kept, thrown, usage)."""
    if len(card_text) + len(transcript_text) > MAX_SOURCE_CHARS:
        raise ImprovementsError("Those documents were too large to send. "
                                "Contact Spenser.", "too_large")
    wanted = "\n".join(
        f"  {block}: " + ", ".join(fields) for block, fields in shape)
    user = (f"The blocks and fields to fill:\n{wanted}\n\n"
            f"=== CARD ===\n{card_text}\n\n=== TRANSCRIPT ===\n{transcript_text}")
    response = _call(READ_RULES, user, Sheet)
    sheet = response.parsed_output
    if sheet is None:
        return [], [], _usage_of(response)
    kept, thrown = verify(sheet.found,
                          {"card": card_text, "transcript": transcript_text})
    return {"parts": sheet.parts, "kept": kept}, thrown, _usage_of(response)


def write_paragraph(block: str, facts: list, notes: str) -> tuple:
    """Pass two. Sees the approved facts and the notes, and nothing else."""
    lines = "\n".join(f"  - {f}" for f in facts if str(f).strip())
    if not lines and not notes.strip():
        raise ImprovementsError("There is nothing approved for this paragraph "
                                "yet. Tick a fact or write a note first.", "empty")
    user = (f"The paragraph to write: {block}\n\n"
            f"Facts he has approved:\n{lines or '  (none)'}\n\n"
            f"His own notes:\n{notes.strip() or '  (none)'}")
    response = _call(WRITE_RULES, user, Paragraph)
    out = response.parsed_output
    return (out.text if out else ""), _usage_of(response)

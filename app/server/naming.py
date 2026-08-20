"""What the built photo document is called, and where the name comes from.

`City_Address Photos (Complete).docx`, from the job's own brief. Two things
about that are easy to get wrong and are worth stating plainly.

The first is that this is parsing, not a lookup. The brief holds one joined
string, "100 Example Avenue, Anytown, Iowa", written by the app in a known order.
Recovering the city and the street from it means splitting on commas, and a
street containing a comma, a unit number, or a brief a human typed can all
split another way. So the values are shown to Mark before Build and he can
correct them, and the correction wins from then on.

The second is that it never guesses. The folder name carries the same two
values, and reading them back out of it would look clever and be wrong: the
folder is named at intake from what he typed, and he may have renamed it since.
When neither the brief nor a correction yields both values, Build refuses and
says which one is missing. A refusal costs him ten seconds. A confidently wrong
filename reaches a client.
"""
import re
from pathlib import Path

import brief
import jobfacts
import jobs

SUFFIX = " Photos (Complete)"


def sanitize(text: str, limit: int = 120) -> str:
    """One name-cleaning rule, shared with the folder namer.

    Lifted out of `jobs.propose_folder_name` so the two cannot drift. Strips
    the characters Windows refuses, drops control characters, collapses runs of
    whitespace, and trims the trailing dots and spaces Explorer will not keep.
    """
    kept = "".join(ch for ch in str(text)
                   if ch not in jobs.WINDOWS_FORBIDDEN and ch >= " ")
    kept = re.sub(r"\s+", " ", kept).strip()
    return kept[:limit].strip().rstrip(". ")


def parse_address(joined: str) -> dict:
    """Split "street, city, state" into its parts, and say how sure it is.

    Three parts is the shape the app writes. Two is a brief with no state.
    One is not enough to name anything, and says so rather than pretending the
    single value is a street.
    """
    parts = [p.strip() for p in str(joined or "").split(",") if p.strip()]
    if len(parts) >= 3:
        return {"address": parts[0], "city": parts[-2], "state": parts[-1],
                "confident": True}
    if len(parts) == 2:
        return {"address": parts[0], "city": parts[1], "state": "",
                "confident": True}
    if len(parts) == 1:
        return {"address": parts[0], "city": "", "state": "", "confident": False}
    return {"address": "", "city": "", "state": "", "confident": False}


def facts_for(job: Path) -> dict:
    """The city and address Build would use, and where each one came from.

    Mark's correction always wins. `source` is carried so the screen can say
    whether he is looking at something read out of the brief or something he
    typed himself.
    """
    parsed = parse_address(brief.read_brief(job)["fields"].get("Property address", ""))
    saved = jobfacts.for_job(job)

    city = saved.get(jobfacts.CITY) or parsed["city"]
    address = saved.get(jobfacts.ADDRESS) or parsed["address"]
    return {
        "city": city,
        "address": address,
        "parsed_city": parsed["city"],
        "parsed_address": parsed["address"],
        "corrected": bool(saved),
        "source": "correction" if saved else ("brief" if parsed["confident"] else "unclear"),
        "ready": bool(city.strip() and address.strip()),
        "missing": [name for name, value in (("city", city), ("address", address))
                    if not value.strip()],
    }


def output_base(city: str, address: str) -> str:
    """`City_Address Photos (Complete)`, cleaned for Windows.

    Raises ValueError when either half is missing, so a caller cannot end up
    with `_Something Photos (Complete)` and not notice.
    """
    clean_city = sanitize(city, limit=50)
    clean_address = sanitize(address, limit=60)
    if not clean_city or not clean_address:
        raise ValueError("both a city and an address are needed to name the file")
    return sanitize("%s_%s%s" % (clean_city, clean_address, SUFFIX), limit=150)

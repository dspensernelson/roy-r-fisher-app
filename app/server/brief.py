"""Read and write a job's job-brief.md.

The brief is the job's own record of the assignment: plain markdown holding
two pipe tables. Other readers already depend on this shape, so this module
is the single place that knows it. jobs.brief_context() parses the Assignment
table for the job card's context line, and the assembler reads the
Sections table to decide what goes into the report.
"""
import re
from pathlib import Path
from typing import Optional

ASSIGNMENT_FIELDS = [
    "Property address",
    "Property type",
    "Engagement type",
    "Client (intended user)",
    "Intended use",
    "Effective date of value",
    "Report due date",
    "Office file number",
]

# Spenser's call, 2026-07-19: the fee is a pointer, never a number. A dollar
# amount in the brief would become a drafting input and trip the
# dollar-literal gate, so no caller can put one here.
FEE_POINTER = "see the engagement letter (pointer only, never the amount)"

# A dollar amount can arrive through any free text field, not only the fee.
# "City of Mason City, fee $4,500 per letter" typed into Client would put a
# number in the brief just as surely as a Fee row would, and the brief is a
# drafting input. The amount is not lost: it is in the engagement letter,
# which this brief points at.
MONEY = re.compile(r"[$£€]\s?[\d,]+(?:\.\d+)?")


def brief_path(job: Path) -> Path:
    return job / "job-brief.md"


def _cells(line: str) -> Optional[list]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [c.strip() for c in stripped[1:-1].split("|")]


def read_brief(job: Path) -> dict:
    """Assignment fields and the section list, from whatever is on disk.

    Tolerant by design: a brief written by hand, by the older onboarding
    skill, or by this app all read the same. Unknown labels are ignored
    rather than rejected, so a brief carrying extra rows still works.
    """
    path = brief_path(job)
    if not path.is_file():
        return {"fields": {}, "sections": []}

    fields: dict = {}
    sections: list = []
    in_sections = False
    for line in path.read_text(errors="ignore").splitlines():
        heading = line.strip().lower()
        if heading.startswith("## "):
            in_sections = heading.startswith("## sections in this report")
            continue
        cells = _cells(line)
        if not cells or len(cells) < 2:
            continue
        label = cells[0].strip()
        if not label or set(label) <= {"-", ":"}:
            continue
        if in_sections:
            if label.lower() != "section":
                sections.append(label)
        elif label in ASSIGNMENT_FIELDS:
            fields[label] = cells[1].strip()
    return {"fields": fields, "sections": sections}


def write_brief(job: Path, fields: dict, sections: Optional[list] = None) -> Path:
    """Write the brief, merging new field values over what is already there.

    Empty incoming values never blank an existing answer, because intake
    fills the brief in more than one pass: three fields at creation, the
    rest whenever the appraiser knows them. Sections are REPLACED rather than merged,
    because unchecking a section has to be able to remove it.
    """
    existing = read_brief(job)
    merged = dict(existing["fields"])
    for name, value in fields.items():
        if name not in ASSIGNMENT_FIELDS:
            continue
        cleaned = re.sub(r"\s{2,}", " ", MONEY.sub("", str(value))).strip(" ,;")
        if cleaned:
            merged[name] = cleaned

    keep = existing["sections"] if sections is None else list(sections)
    rows = "\n".join(f"| {name} | {merged.get(name, '')} |" for name in ASSIGNMENT_FIELDS)
    section_rows = "\n".join(f"| {s} | |" for s in keep) if keep else "| | |"

    text = (
        f"# Job Brief - {job.name}\n\n"
        "## Assignment\n\n"
        "| Field | Value |\n|---|---|\n"
        f"{rows}\n"
        f"| Fee | {FEE_POINTER} |\n\n"
        "## Sections in this report\n\n"
        "| Section | Donor |\n|---|---|\n"
        f"{section_rows}\n"
    )
    path = brief_path(job)
    path.write_text(text)
    return path

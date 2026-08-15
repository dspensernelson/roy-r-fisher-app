"""Propose a report's section list from the engagement matrix.

The matrix (app/data/engagement-matrix.md) is the firm's measured record of
which sections each engagement shape carries. It stays the single source of
truth: this module reads it rather than restating it, so a correction to the
matrix reaches the app with no code change.

What the app adds on top is only what the matrix cannot express in a cell:
one row that is really two sections, one row that is not a standalone
section at all, and the difference between "always" and "sometimes".
"""
from pathlib import Path

MATRIX = Path(__file__).resolve().parents[1] / "data" / "engagement-matrix.md"

# What Mark picks, mapped to the matrix's own column headings.
ENGAGEMENTS = {
    "Full appraisal": "Full appraisal",
    "Tax appeal": "Tax appeal",
    "Restricted short form": "Short-form (sales only)",
    "Rent study": "Rent study",
    "Right of way": "ROW value finding",
}

# The matrix's own header says these three columns rest on ONE delivered
# report each. The screen states that instead of presenting a guess as a
# standard; the matrix's hard gate says to confirm the shape before drafting.
THIN_EVIDENCE = {"Short-form (sales only)", "Rent study", "ROW value finding"}

# The matrix's Assessment row says the assessment grid folds INTO Salient
# Facts rather than standing alone, and the section rulebook calls a
# standalone Assessment section the invented-section case. So it is never
# offered as a section of its own.
NOT_STANDALONE = {"Assessment and Taxes"}

# One matrix row that is really two documents in every delivered report.
SPLIT = {"Title + transmittal": ["Title Page", "Letter of Transmittal"]}

# A cell that qualifies its yes ("out-of-metro only", "optional, evidence
# thin", "rarely", "if improvements affected") means the section sometimes
# applies. It is offered unchecked so Mark decides, rather than checked so
# he has to notice and undo it.
QUALIFIERS = ("optional", "only", "rarely", "if ")


def _table(text: str):
    """The matrix's section table as (header cells, data rows).

    Picks the table whose first column is literally "Section" and takes only
    later rows with the same column count, so the property-type and
    two-structure tables further down the file are ignored.
    """
    header = None
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [c.strip() for c in stripped[1:-1].split("|")]
        if all(set(c) <= {"-", ":"} for c in cells if c):
            continue
        if header is None:
            if cells and cells[0].lower() == "section":
                header = cells
            continue
        if len(cells) == len(header):
            rows.append(cells)
    return header, rows


def propose(engagement: str) -> dict:
    column = ENGAGEMENTS.get(engagement)
    if column is None:
        raise ValueError(f"unknown engagement type: {engagement}")
    if not MATRIX.is_file():
        raise FileNotFoundError(str(MATRIX))

    header, rows = _table(MATRIX.read_text(errors="ignore"))
    if header is None or column not in header:
        raise ValueError(f"the engagement matrix has no column named {column}")
    index = header.index(column)

    out = []
    for cells in rows:
        name = cells[0].strip()
        if not name or name in NOT_STANDALONE:
            continue
        value = cells[index].strip().lower()
        default = bool(value) and value != "no" and not any(q in value for q in QUALIFIERS)
        for real_name in SPLIT.get(name, [name]):
            out.append({"name": real_name, "default": default})

    return {"engagement": engagement, "column": column,
            "thin_evidence": column in THIN_EVIDENCE, "sections": out}

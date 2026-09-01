"""Turn a job's assessor card and inspection transcript into plain text.

Two file kinds, because those are the two the section is built from. The
assessor card is a PDF the county issues; the transcript is a Word file of
Mark's own walkthrough. Nothing else is read.

Measured on the Blaul Lofts job 2026-08-28: the card supplies four exact
values and the transcript supplies most of the rest. Neither is optional, and
the section is not offered until both are present.
"""
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# What Mark's office calls these files. Measured across the delivered jobs:
# the card is always PRC-prefixed, the transcript always carries the word.
CARD_HINTS = ("prc", "property record", "parcel")
TRANSCRIPT_HINTS = ("transcript",)

# Folders whose contents describe a DIFFERENT building. Measured on Blaul
# Lofts 2026-08-28: searching the whole job found four property record cards,
# three of them comparable sales in Moline and Des Moines, and the first one
# alphabetically was a comp. Reading a comparable's card into the subject's
# Description of Improvements would put another building's walls in Mark's
# report over his signature.
#
# These are folder names in Mark's own template, so unlike the photograph
# folders they are stable. They are still only used to rank and exclude what
# is offered. Mark picks the file.
NOT_THE_SUBJECT = {"comps", "comps 2", "old reports", "old report", "drafts"}

# Where the subject's own paperwork lives in that template.
SUBJECT_FOLDERS = {"subject information", "transcripts", "transcript information",
                   "improvements"}

def _docx_text(path: Path) -> str:
    root = ET.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
    out = []
    for para in root.iter(_W + "p"):
        line = "".join(node.text or "" for node in para.iter(_W + "t"))
        if line.strip():
            out.append(line)
    return "\n".join(out)


def _pdf_text(path: Path) -> str:
    import pypdf
    reader = pypdf.PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return _pdf_text(path)
    if path.suffix.lower() == ".docx":
        return _docx_text(path)
    raise ValueError(f"cannot read {path.suffix} for this section")


def _wanted(name: str, hints) -> bool:
    low = name.lower()
    return any(h in low for h in hints)


def _rank(path: Path, job_dir: Path, wanted_word: str) -> tuple:
    """Best first. A file in the subject's own folder outranks a loose one,
    and a transcript naming this section outranks the neighbourhood one."""
    parts = [p.lower() for p in path.relative_to(job_dir).parts[:-1]]
    in_subject = any(p in SUBJECT_FOLDERS for p in parts)
    names_section = wanted_word in path.name.lower()
    return (not names_section, not in_subject, len(parts), path.name.lower())


def find_sources(job_dir: Path) -> dict:
    """Which files in this job look like the two sources.

    Names only, and only to offer them. The app never decides from a name what
    a document holds: Mark confirms the pick before anything is read. This is
    the propose-against-assert rule from 2026-08-25.
    """
    cards, transcripts = [], []
    for path in sorted(job_dir.rglob("*")):
        if not path.is_file() or path.name.startswith("~$"):
            continue
        parts = [p.lower() for p in path.relative_to(job_dir).parts[:-1]]
        if any(p in NOT_THE_SUBJECT for p in parts):
            continue
        suffix = path.suffix.lower()
        if suffix == ".pdf" and _wanted(path.name, CARD_HINTS):
            cards.append(path)
        elif suffix == ".docx" and _wanted(path.name, TRANSCRIPT_HINTS):
            transcripts.append(path)
    cards.sort(key=lambda p: _rank(p, job_dir, "prc"))
    transcripts.sort(key=lambda p: _rank(p, job_dir, "improvement"))
    return {"cards": cards, "transcripts": transcripts}


def flatten(text: str) -> str:
    """Letters and digits only, lowercased.

    Both sources arrive through extractors that scatter spacing: the PDF
    breaks words across columns and the transcript carries curly quotes and
    non-breaking spaces. A quote check that respected any of that would reject
    values that really are in the source, which is worse than useless.
    """
    return re.sub(r"[^a-z0-9]", "", text.lower())

"""The template that ships inside the app is the one Mark's PC will use.

Every other build test points at the private corpus copy, which a clone may
not have. These tests point at app/templates/Photo.docx, which is always
present, so the path that actually runs on Mark's machine is never the one
path with no test on it. No skip marker on purpose.
"""
import json
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Emu
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from photo_pages import build_photo_docx  # noqa: E402

SHIPPED = Path(__file__).resolve().parents[1] / "templates" / "Photo.docx"


def test_shipped_template_matches_measured_furniture():
    d = Document(str(SHIPPED))
    s = d.sections[0]
    assert round(Emu(s.page_width).inches, 1) == 8.5
    assert round(Emu(s.left_margin).inches, 1) == 0.9
    assert len(d.tables) == 14
    for t in d.tables:
        assert len(t.rows) == 3 and len(t.columns) == 2
    assert d.paragraphs[0].text.strip() == "SUBJECT PHOTOGRAPHS"
    assert len(d.inline_shapes) == 0


def test_shipped_template_builds_photo_pages(tmp_path):
    names = []
    for i in range(5):
        p = tmp_path / f"IMG_{5100 + i}.jpg"
        Image.new("RGB", (400, 300), (i * 30 % 255, 80, 90)).save(p)
        names.append(p.name)
    manifest = tmp_path / "photo-manifest.json"
    manifest.write_text(json.dumps({
        "job": "TESTJOB", "context": "123 Test St, Davenport, Iowa",
        "report_year": 2026,
        "photos": [{"file": n, "caption": f"View of test subject {i}"}
                   for i, n in enumerate(names)],
    }))
    out = build_photo_docx(manifest, SHIPPED)
    d = Document(str(out))
    assert len(d.tables) == 2          # ceil(5/3) pages
    assert len(d.inline_shapes) == 5   # one image per photo


SIX_UP_SHIPPED = Path(__file__).resolve().parents[1] / "templates" / "Photo six-up.docx"


def _row_heights(table):
    """Each row's declared height in inches, read off w:trHeight."""
    out = []
    for row in table.rows:
        trPr = row._tr.find(qn("w:trPr"))
        e = None if trPr is None else trPr.find(qn("w:trHeight"))
        out.append(None if e is None else round(int(e.get(qn("w:val"))) / 1440, 2))
    return out


def test_shipped_six_up_template_matches_the_measured_budget():
    """2.60in photo rows and 0.46in caption rows are not a preference.

    They are the vertical budget in docs/plans/2026-09-07-six-up-photo-pages.md:
    10.00in between the margins, less 0.42in for the heading and its spacer,
    less the 9.18in this table occupies, leaving 0.40in of slack on purpose.
    Change either number without redoing that arithmetic and the page
    overflows, which is the defect the three-up template already has.
    """
    d = Document(str(SIX_UP_SHIPPED))
    s = d.sections[0]
    assert round(Emu(s.page_width).inches, 1) == 8.5
    assert round(Emu(s.left_margin).inches, 1) == 0.9
    assert round(Emu(s.top_margin).inches, 1) == 0.5
    assert round(Emu(s.bottom_margin).inches, 1) == 0.5
    assert len(d.tables) == 14
    for t in d.tables:
        assert len(t.rows) == 6 and len(t.columns) == 2
        widths = [round(Emu(c.width).inches, 2) for c in t.rows[0].cells]
        assert widths == [3.35, 3.35], widths
        assert _row_heights(t) == [2.6, 0.46, 2.6, 0.46, 2.6, 0.46]
    assert d.paragraphs[0].text.strip() == "SUBJECT PHOTOGRAPHS"
    assert len(d.inline_shapes) == 0


def test_the_two_shipped_templates_agree_on_the_page_itself():
    """Six-up is Mark's template with nothing changed but the tables. If the
    page or the margins ever drift apart, one of them stopped being his."""
    three, six = Document(str(SHIPPED)), Document(str(SIX_UP_SHIPPED))
    a, b = three.sections[0], six.sections[0]
    for attr in ("page_width", "page_height", "left_margin", "right_margin",
                 "top_margin", "bottom_margin"):
        assert getattr(a, attr) == getattr(b, attr), attr
    # Both tables span the same 6.70in of usable width.
    for d in (three, six):
        total = sum(Emu(c.width).inches for c in d.tables[0].rows[0].cells)
        assert round(total, 2) == 6.70

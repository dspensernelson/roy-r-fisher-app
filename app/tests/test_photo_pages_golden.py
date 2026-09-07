import json
import shutil
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from photo_pages import SIX_UP, build_photo_docx, exif_order  # noqa: E402

from conftest import GOLDEN_DELIVERED, GOLDEN_PHOTOS, TEMPLATE_DOCX, has_golden_corpus

SIX_UP_TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "Photo six-up.docx"

MASON_PHOTOS = GOLDEN_PHOTOS
DELIVERED = GOLDEN_DELIVERED


@has_golden_corpus
def test_mason_city_golden(tmp_path):
    raws = exif_order(sorted(MASON_PHOTOS.glob("*.jpeg")))[:12]
    assert len(raws) == 12, "expected at least 12 raw Mason City jpegs"
    for p in raws:
        shutil.copy2(p, tmp_path / p.name)
    manifest = tmp_path / "photo-manifest.json"
    manifest.write_text(json.dumps({
        "job": "MASON CITY", "context": "4151 4th St SW, Mason City, Iowa",
        "report_year": 2026,
        "photos": [{"file": p.name, "caption": f"View of subject, photo {i + 1}"} for i, p in enumerate(raws)],
    }))
    out = build_photo_docx(manifest, TEMPLATE_DOCX)
    built, delivered = Document(str(out)), Document(str(DELIVERED))
    assert len(built.tables) == 4                          # 12 photos / 3 per page
    assert len(built.inline_shapes) == 12
    # Parity with Mark's artifact: same table geometry, same margins
    assert (len(built.tables[0].rows), len(built.tables[0].columns)) == \
           (len(delivered.tables[0].rows), len(delivered.tables[0].columns))
    assert built.sections[0].left_margin == delivered.sections[0].left_margin


@has_golden_corpus
def test_mason_city_builds_six_up_from_the_same_photographs(tmp_path):
    """The same real job, the same real photographs, the other layout.

    Twelve photographs are four three-up pages and two six-up ones. Every
    caption must survive into the six-up document in the order it was given:
    the layout changes where a caption sits, never which photograph it
    belongs to.
    """
    raws = exif_order(sorted(MASON_PHOTOS.glob("*.jpeg")))[:12]
    assert len(raws) == 12
    for p in raws:
        shutil.copy2(p, tmp_path / p.name)
    captions = [f"View of subject, photo {i + 1}" for i in range(12)]
    manifest = tmp_path / "photo-manifest.json"
    manifest.write_text(json.dumps({
        "job": "MASON CITY", "context": "4151 4th St SW, Mason City, Iowa",
        "report_year": 2026,
        "photos": [{"file": p.name, "caption": c} for p, c in zip(raws, captions)],
    }))

    three = Document(str(build_photo_docx(manifest, TEMPLATE_DOCX)))
    six = Document(str(build_photo_docx(manifest, SIX_UP_TEMPLATE, layout=SIX_UP)))

    assert len(three.tables) == 4 and len(six.tables) == 2
    assert len(three.inline_shapes) == len(six.inline_shapes) == 12

    def captions_of(doc):
        return [c.text.strip() for t in doc.tables for r in t.rows
                for c in r.cells if c.text.strip()]

    assert captions_of(three) == captions
    assert captions_of(six) == captions

    # Both are built on Mark's page. The layout changes the table, not the page.
    for attr in ("page_width", "page_height", "left_margin", "top_margin"):
        assert getattr(three.sections[0], attr) == getattr(six.sections[0], attr)

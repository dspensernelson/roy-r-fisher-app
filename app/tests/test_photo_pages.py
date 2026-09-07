import json
import math
import sys
import zipfile
from pathlib import Path

import pytest
from docx import Document
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from photo_pages import (LAYOUTS, SIX_UP, THREE_UP, build_photo_docx,  # noqa: E402
                         exif_order, next_output_name)

from conftest import TEMPLATE_DOCX, has_template


def make_photos(d: Path, n: int) -> list[str]:
    names = []
    for i in range(n):
        p = d / f"IMG_{5100 + i}.jpg"
        Image.new("RGB", (400, 300), (i * 30 % 255, 80, 90)).save(p)
        names.append(p.name)
    return names


def write_manifest(photos_dir: Path, names: list[str]) -> Path:
    m = photos_dir / "photo-manifest.json"
    m.write_text(json.dumps({
        "job": "TESTJOB", "context": "123 Test St, Davenport, Iowa",
        "report_year": 2026,
        "photos": [{"file": n, "caption": f"View of test subject {i}"} for i, n in enumerate(names)],
    }))
    return m


@has_template
def test_build_fills_three_per_page_and_trims_tables(tmp_path):
    names = make_photos(tmp_path, 5)
    out = build_photo_docx(write_manifest(tmp_path, names), TEMPLATE_DOCX)
    d = Document(str(out))
    assert len(d.tables) == 2                      # ceil(5/3) pages
    assert len(d.inline_shapes) == 5               # one image per photo
    # Five photographs, five rows. The sixth slot used to be an empty row on
    # the last page; Spenser found it on the 61-photo job, where it was two.
    assert [len(t.rows) for t in d.tables] == [3, 2]
    caps = [r.cells[1].text.strip() for t in d.tables for r in t.rows]
    assert len(caps) == 5
    assert "View of test subject 0" in caps[0]
    assert all(c for c in caps), "every row holds a caption"


@has_template
def test_build_never_overwrites(tmp_path):
    names = make_photos(tmp_path, 1)
    m = write_manifest(tmp_path, names)
    first = build_photo_docx(m, TEMPLATE_DOCX)
    second = build_photo_docx(m, TEMPLATE_DOCX)
    assert first.exists() and second.exists() and first != second


def test_next_output_name_is_fresh(tmp_path):
    (tmp_path / "Photo.docx").write_bytes(b"x")
    name = next_output_name(tmp_path)
    assert name.endswith(".docx") and not (tmp_path / name).exists()


def test_exif_order_falls_back_to_name(tmp_path):
    names = make_photos(tmp_path, 3)          # generated JPEGs carry no EXIF
    ordered = exif_order([tmp_path / n for n in reversed(names)])
    assert [p.name for p in ordered] == names


def _footer_texts(doc):
    """All (default, first-page, even-page) footer texts across every section.

    python-docx's `section.footer` is only the *default* footer part -- the
    template stores separate XML parts for the first-page and even-page
    footers, selected at render time because `titlePg` is set. A fix that
    only checks `.footer` would have passed while the first-page footer
    (what page 1 actually shows) was still stale -- exactly how the round-1
    fix shipped with that gap.
    """
    return [
        "".join(run.text for p in getattr(section, variant).paragraphs for run in p.runs)
        for section in doc.sections
        for variant in ("footer", "first_page_footer", "even_page_footer")
    ]


def _first_page_header_text(doc, section_index):
    section = doc.sections[section_index]
    return "".join(run.text for p in section.first_page_header.paragraphs for run in p.runs)


@has_template
def test_build_sets_footer_year_and_preserves_page_fields(tmp_path):
    names = make_photos(tmp_path, 1)
    m = write_manifest(tmp_path, names)  # report_year: 2026; template's footer parts say 2022 / 2023
    out = build_photo_docx(m, TEMPLATE_DOCX)
    d = Document(str(out))
    footers = _footer_texts(d)
    combined = "".join(footers)
    assert "2026" in combined
    assert "2022" not in combined and "2023" not in combined
    assert "Page" in combined
    assert "of" in combined
    # Finding A regression: the *first-page* footer is a separate XML part
    # from the default footer and carries its own, differently-stale year
    # ("2023" vs. the default footer's "2022"). It is what page 1 actually
    # renders (titlePg is set), so it must be rewritten too, not just the
    # default footer.
    first_page_footer_text = "".join(
        run.text for p in d.sections[0].first_page_footer.paragraphs for run in p.runs
    )
    assert "2026" in first_page_footer_text


@has_template
@pytest.mark.parametrize(
    "n, expect_two_sections",
    [(1, False), (2, False), (3, False), (4, True), (7, True)],
)
def test_build_page_shape_has_no_orphaned_continuation_section(tmp_path, n, expect_two_sections):
    """Structural proxy for Finding B: rendered page count must equal
    ceil(n/3) with no trailing blank/continuation page, and the "SUBJECT
    PHOTOGRAPHS- CONTINUED" running header must still appear on pages 2+
    when there are pages 2+.

    This cannot prove Word's actual rendered page count -- only a real
    render can, and this repo has no Word automation available -- but it
    pins the section/header shape that produces the right behavior: when
    every photo fits on the title page (needed == 1 table), the template's
    normally-vestigial second section must be fully merged away rather than
    left empty for Word to paginate; whenever a real continuation page is
    needed (needed >= 2 tables), the template's original two-section shape,
    with the CONTINUED header intact on the continuation section's own
    first page, must be preserved unchanged.
    """
    names = make_photos(tmp_path, n)
    m = write_manifest(tmp_path, names)
    out = build_photo_docx(m, TEMPLATE_DOCX)
    d = Document(str(out))
    assert len(d.tables) == math.ceil(n / 3)

    if expect_two_sections:
        assert len(d.sections) == 2
        assert "CONTINUED" in _first_page_header_text(d, 1)
    else:
        assert len(d.sections) == 1
    # Page 1 is always section 0's own first page; it must never show the
    # continuation header, regardless of whether a second section exists.
    assert "CONTINUED" not in _first_page_header_text(d, 0)


# --- The layout object, added 2026-09-07 for six-up ------------------------
#
# These need no template and no corpus: they are arithmetic about where a
# photograph goes, which is the thing six-up changes and the thing that used
# to be a bare 3 in two different files.


def test_three_up_puts_the_caption_beside_the_photograph():
    """One row per photograph, image left and caption right. This is what the
    template has always been and it must not move."""
    assert [THREE_UP.cells(n) for n in range(3)] == [
        (0, 0, 0, 1), (1, 0, 1, 1), (2, 0, 2, 1)]


def test_six_up_reads_left_to_right_then_down():
    """Spenser, 2026-09-07, asked whether a band should read down a column
    instead: left to right, top to bottom. So a photograph sits in one of two
    columns and its caption sits directly beneath it."""
    assert [SIX_UP.cells(n) for n in range(6)] == [
        (0, 0, 1, 0), (0, 1, 1, 1),
        (2, 0, 3, 0), (2, 1, 3, 1),
        (4, 0, 5, 0), (4, 1, 5, 1)]


def test_three_up_trims_one_row_per_photograph():
    assert [THREE_UP.rows_for(k) for k in (1, 2, 3)] == [1, 2, 3]


def test_six_up_trims_in_whole_pairs_and_an_odd_one_leaves_a_gap():
    """Spenser chose this on 2026-09-07 over merging the last pair into one
    full-width cell: a photograph that changes size according to how many
    there happen to be is a rule that surprises somebody six months later."""
    assert [SIX_UP.rows_for(k) for k in (1, 2, 3, 4, 5, 6)] == [2, 2, 4, 4, 6, 6]


def test_the_layouts_are_reachable_by_how_many_go_on_a_page():
    """One value in the manifest decides both the template and the shape, so
    the two can never disagree."""
    assert LAYOUTS[3] is THREE_UP and LAYOUTS[6] is SIX_UP
    assert (THREE_UP.template, SIX_UP.template) == ("Photo.docx", "Photo six-up.docx")


def _body_xml(path: Path) -> bytes:
    """The document body as Word stores it, for comparing two builds.

    Compared as bytes rather than by walking the tree, because the point is
    that nothing moved at all: not a cell, not an attribute, not a run.
    """
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml")


@has_template
def test_the_layout_object_did_not_move_three_up(tmp_path):
    """The Layout refactor must be a refactor and nothing else.

    Every count in the engine used to be a bare 3 and now comes off THREE_UP.
    If any of them came off wrong, the document changes, and the document is
    what Mark signs. So this compares the real bytes rather than a shape.
    """
    names = make_photos(tmp_path, 5)
    m = write_manifest(tmp_path, names)
    default = build_photo_docx(m, TEMPLATE_DOCX)
    explicit = build_photo_docx(m, TEMPLATE_DOCX, layout=THREE_UP)
    assert _body_xml(default) == _body_xml(explicit)


@has_template
@pytest.mark.parametrize("count", [1, 2, 3, 4, 5, 7, 11, 12, 13])
def test_three_up_page_and_row_counts_are_what_they_always_were(tmp_path, count):
    """The counts Spenser found the trimming bugs on: 11 and 12 and 61 all
    behaved differently before `_trim_unused_rows` and
    `_drop_trailing_blank_paragraphs` existed. Pin them so the layout object
    cannot quietly change one."""
    names = make_photos(tmp_path, count)
    out = build_photo_docx(write_manifest(tmp_path, names), TEMPLATE_DOCX)
    d = Document(str(out))
    assert len(d.tables) == max(1, math.ceil(count / 3))
    assert len(d.inline_shapes) == count
    on_last = count - (len(d.tables) - 1) * 3
    assert len(d.tables[-1].rows) == on_last

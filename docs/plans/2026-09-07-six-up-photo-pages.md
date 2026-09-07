# Plan: six photographs to a page

> For whoever executes this: the work list is the contract. Tick a box only
> when the thing is true, not when it is written.

## Context

Mark's office wants six photographs on a page instead of three, and wants to
pick which a job uses. Three-up stays exactly as it is.

**Approved by Spenser on 2026-09-07.** The layout is F4 in `docs/FUTURES.md`,
written 2026-09-03, and P1 in `docs/PUNCHLIST.md` is the same answer. F4, not
this plan, is the record of why the layout is what it is.

Three down the left, three down the right, each pair of captions under its
pair of photographs. Reading left to right, top to bottom.

    photo    photo
    caption  caption
    photo    photo
    caption  caption
    photo    photo
    caption  caption

### Answered by Spenser on 2026-09-07

- **The template is manufactured, not Mark's.** There is no six-up page
  anywhere in the corpus to clone. He opened the built file in Word and
  approved it.
- **The choice is a toggle on the Photos title row**, not a step inside the
  Build click. `HOW-WE-WORK.md` says a choice that shapes an action lives
  inside that action; he overruled it here, and the reason holds: this
  describes the job the way `bands_on` does, and it changes the screen before
  Build is ever pressed.
- **An odd photograph on the last page leaves one empty bordered box**, rather
  than merging the last pair into one full-width cell. A photograph that
  changes size according to how many photographs there happen to be is a rule
  that surprises somebody six months later.
- **Bands read left to right, top to bottom**, the same order the page already
  has. So bands need no mapping of their own and nothing in the band code has
  to know which layout a job uses.

### What is here today

- `app/engine/photo_pages.py:34` `PHOTOS_PER_TABLE = 3` is a bare number, and
  `app/engine/photo_pages.py:503` assumes one row is one photograph, image in
  `cells[0]` and caption in `cells[1]`. Neither survives six-up.
- `app/engine/photo_pages.py:55` `IMAGE_WIDTH_IN = 4.0` and
  `IMAGE_MAX_HEIGHT_IN = 3.0` are module constants read by `_fitted_size`.
- `app/engine/photo_pages.py:410` `_trim_unused_rows` cuts the rows on the last
  page that hold no photograph, one row per photograph.
- `app/engine/photo_pages.py:432` `_drop_trailing_blank_paragraphs` exists
  because the three-up template declares rows 2.926in tall and the app puts a
  3.00in photograph in them. Six-up does not repeat that mistake and this
  function stays exactly as it is.
- `app/server/main.py:52` `DEFAULT_PHOTO_TEMPLATE` is the one template, and
  `app/server/main.py:1115` reads `RRF_PHOTO_TEMPLATE` over it.
- `app/server/main.py:56` `photo_pages_per_table()` was built to serve this
  number to the browser and **is called from nowhere.** It is dead code.
- `app/web/src/screens/PhotosScreen.jsx:336` therefore wrote its own copy:
  `Math.ceil(inPhotos.length / 3)`. Six-up is what makes that copy start lying.
- `app/web/src/screens/PhotosScreen.jsx:864` draws a `page-preview` grid inside
  the caption chooser, in its own words "exactly the way photo_pages.py builds
  the real thing". It is the three-up shape.
- `app/server/photos.py:557` `_validate_manifest_shape` is the only guard on
  what may be written into the manifest. `bands_on` is checked at
  `app/server/photos.py:734` and `photos_per_page` goes in beside it.
- `app/web/src/brand.css:367` `.toggle` is the segmented control the caption
  chooser already uses. The new toggle uses it and adds no new control.

### The measured furniture

Everything below came off Mark's delivered reports, not off one example.
Re-measure rather than trusting this list if anything looks wrong.

**All sixteen photo documents in `RRF/Report Examples` are three per page.**
Photographs at 4.00 x 3.00in, rows declared 2.926in, cells 4.58in and 2.12in.
The tables that read as six or twelve rows are consecutive tables Word merged,
not six on a page.

**Two hundred distinct real captions, measured for wrapping.**

| Caption column | 1 line | 2 lines | 3 lines | 4 lines |
|---|---|---|---|---|
| 2.12in, three-up today | 28% | 54% | 18% | 1% |
| 3.20in, six-up | 68% | 32% | 0.5% | 0% |

The wider caption column is not a side effect. It is an improvement to the
thing Mark actually types.

**The vertical budget, page 1, which is the tightest because it carries the
heading.**

    10.00 in  top margin to bottom margin
    -0.42 in  SUBJECT PHOTOGRAPHS and the spacer under it
    -9.18 in  the table: 3 photo rows at 2.60in, 3 caption rows at 0.46in
    = 0.40 in  left over, and it is left over on purpose

The 0.40in is slack for captions that wrap further than measured. A page built
from the six longest captions in the corpus fits with all of it still spare.

| | Three-up | Six-up |
|---|---|---|
| Table shape | 3 rows x 2 cols | 6 rows x 2 cols |
| Columns | 4.58in photo, 2.12in caption | 3.35in and 3.35in |
| Table width | 6.70in | 6.70in, unchanged |
| Rows | 2.926in | 2.60in photo, 0.46in caption |
| Image box | 4.00 x 3.00in | 3.20 x 2.40in |

## Rules for whoever executes this

- **Three-up must not move.** Every slice proves it: the same photographs
  through the shipped engine produce the document they produce today. A job
  with no `photos_per_page` key is three per page.
- **Test the claim with the right evidence.** Synthetic images and temporary
  folders prove page arithmetic, trimming and refusals. They may not support a
  claim about Mark's layouts. Anything about his furniture is measured against
  `RRF/Report Examples`, and those tests carry `has_template` or
  `has_golden_corpus` so a clone without the corpus skips rather than lies.
- **Never write into `RRF/Report Examples/`.** Copy out, never in.
- Nothing here needs anything but Python on Mark's Windows PC.

## The work list

### Slice 1, the engine knows two layouts, and three-up builds the same document

- [x] Add the failing cases to `app/tests/test_photo_pages.py` and watch them fail
- [x] Add `Layout`, `THREE_UP` and `SIX_UP` to `app/engine/photo_pages.py`
- [x] `Layout.cells(n)` returns where photograph `n` puts its image and caption
- [x] `Layout.rows_for(k)` returns the rows a last page holding `k` keeps
- [x] `_fitted_size` takes its box from the layout instead of the module constants
- [x] `build_photo_docx` takes `layout=THREE_UP` and uses it for every count
- [x] `_trim_unused_rows` takes the layout and trims in whole rows or whole pairs
- [x] Prove three-up output is unchanged: same photographs, same document
- [x] `cd app/web && npm run build`, then the whole suite passes with nothing skipped
- [x] Commit on `the-engine-knows-two-layouts`, and Spenser says yes

### Slice 2, a page that holds six

- [x] Add `app/tests/test_six_up_pages.py` and watch it fail
- [x] Add `app/templates/Photo six-up.docx` and pin its furniture, no skip marker
- [x] Add it to the packaging manifest at `app/tests/test_package_manifest.py:115`
- [x] Page counts: 1, 6, 7, 12, 13 photographs give 1, 1, 2, 2, 3 pages
- [x] No trailing blank page at any of those counts
- [x] Pair trimming: 1 and 2 keep 2 rows, 3 and 4 keep 4, 5 and 6 keep 6
- [x] An odd count leaves exactly one empty cell, and a test says so by name
- [x] A page of six three-line captions does not run past the bottom margin unnoticed
- [x] The golden Mason City job builds both ways off the real corpus
- [x] `cd app/web && npm run build`, then the whole suite passes with nothing skipped
- [x] Commit on `a-page-that-holds-six`, and Spenser says yes

### Slice 3, the manifest can hold the choice, and nothing behaves differently

- [x] Add the failing cases to `app/tests/test_photos_api.py` and watch them fail
- [x] Add `PHOTOS_PER_PAGE` and `photos_per_page(manifest)` to `app/server/photos.py`
- [x] Teach `_validate_manifest_shape` that it must be 3 or 6 if it is there at all
- [x] Prove a manifest without the key reads as three, with nothing to migrate
- [x] `app/server/main.py` picks the template and the layout together from that one value
- [x] `RRF_PHOTO_TEMPLATE` still overrides, and overriding does not change the layout
- [x] Delete the dead `photo_pages_per_table()` at `app/server/main.py:56`
- [x] The manifest route returns `photos_per_page` always present, without writing it to disk
- [x] Prove a build with the key absent produces the document it produces today
- [x] `cd app/web && npm run build`, then the whole suite passes with nothing skipped
- [x] Commit on `the-manifest-holds-the-layout`, and Spenser says yes

### Slice 4, the toggle on the screen, and the hardcoded 3 goes away

- [x] Add the failing cases to `app/web/src/screens/PhotosScreen.test.jsx`
- [x] Delete `Math.ceil(inPhotos.length / 3)` and read the value the server normalised
- [x] Add the toggle to the Photos title row, using the existing `.toggle` control
- [x] The page count in the subtitle follows the toggle
- [x] The `page-preview` grid in the caption chooser follows the toggle
- [x] Nothing else on the screen changes: tiles, dots, drag order all untouched
- [x] A job with no key shows Three per page selected
- [x] `cd app/web && npm run build`, then the whole suite passes with nothing skipped
- [x] Commit on `six-up-on-the-screen`, and Spenser says yes

### Closing this plan out

- [x] Prove it by hand on a real job, not only by test
- [ ] Ask Spenser, then fold the learnings into `docs/ROADMAP.md`
- [ ] Ask Spenser, then mark F4 built in `docs/FUTURES.md` and clear P1 from `docs/PUNCHLIST.md`
- [ ] Delete this plan

---

## Slice 1: the engine knows two layouts

**The point of this slice is that nothing changes.** Two layouts exist, three-up
is the default everywhere, and the document Mark gets is the document he got
yesterday. Six-up is not reachable until slice 2.

`PHOTOS_PER_TABLE` is referenced by `app/server/main.py:59` and by four test
modules. It goes, and every call site moves to the layout. Leaving it behind as
an alias would be a second copy of the same fact, which is the defect this
slice exists to remove.

**The layout, added near the top of `app/engine/photo_pages.py` where
`PHOTOS_PER_TABLE` is today:**

```python
class Layout(NamedTuple):
    """One printed page's shape. The single place a layout's facts live.

    Everything that used to be a bare 3 in this module reads one of these
    instead. `PHOTOS_PER_TABLE` was that bare 3 and it had already been
    copied into the browser, where it started to lie the moment a second
    layout existed. See HOW-WE-WORK.md: point at where a value lives.
    """
    name: str            # what a manifest and a log call it
    per_page: int        # photographs on one printed page
    rows_per_page: int   # rows in one of the template's tables
    template: str        # the file that ships in app/templates/
    width_in: float      # the box a photograph is fitted inside
    max_height_in: float

    def cells(self, n: int):
        """Where photograph `n` goes, `n` counted within its own page.

        Returns (image_row, image_col, caption_row, caption_col).

        Three-up is one row per photograph, image left and caption right,
        which is what the template has always been. Six-up reads left to
        right and top to bottom, so a photograph sits in one of two columns
        and its caption sits directly beneath it in the row below.
        """
        if self.per_page == self.rows_per_page:      # three-up
            return n, 0, n, 1
        row, col = (n // 2) * 2, n % 2               # six-up
        return row, col, row + 1, col

    def rows_for(self, k: int) -> int:
        """The rows a last page holding `k` photographs keeps.

        Six-up fills in pairs, so a page keeps whole pairs and an odd `k`
        leaves one empty bordered box at the bottom right. That is Spenser's
        decision of 2026-09-07, not an accident: see the plan's Context.
        """
        if self.per_page == self.rows_per_page:      # three-up
            return k
        return 2 * -(-k // 2)                        # six-up, ceil to a pair


THREE_UP = Layout("three-up", 3, 3, "Photo.docx", 4.0, 3.0)
SIX_UP = Layout("six-up", 6, 6, "Photo six-up.docx", 3.20, 2.40)
LAYOUTS = {layout.per_page: layout for layout in (THREE_UP, SIX_UP)}
```

`NamedTuple` comes from `typing`, which is already a standard-library import
and adds nothing to Mark's machine.

**The tests to write first**, in `app/tests/test_photo_pages.py`. These need no
corpus and no template, so they carry no skip marker:

```python
from photo_pages import SIX_UP, THREE_UP


def test_three_up_puts_the_caption_beside_the_photograph():
    assert [THREE_UP.cells(n) for n in range(3)] == [
        (0, 0, 0, 1), (1, 0, 1, 1), (2, 0, 2, 1)]


def test_six_up_reads_left_to_right_then_down():
    """Spenser, 2026-09-07, when asked whether a band should read down a
    column instead: left to right, top to bottom."""
    assert [SIX_UP.cells(n) for n in range(6)] == [
        (0, 0, 1, 0), (0, 1, 1, 1),
        (2, 0, 3, 0), (2, 1, 3, 1),
        (4, 0, 5, 0), (4, 1, 5, 1)]


def test_three_up_trims_one_row_per_photograph():
    assert [THREE_UP.rows_for(k) for k in (1, 2, 3)] == [1, 2, 3]


def test_six_up_trims_in_whole_pairs_and_an_odd_one_leaves_a_gap():
    assert [SIX_UP.rows_for(k) for k in (1, 2, 3, 4, 5, 6)] == [2, 2, 4, 4, 6, 6]
```

Run: `cd app/tests && python3 -m pytest test_photo_pages.py -v`
Expected: FAIL, `ImportError: cannot import name 'SIX_UP'`.

**`_fitted_size` takes the box as an argument** rather than reading the module
constants. Its docstring already explains why both edges are honoured and that
paragraph stays; add that the box now comes from the layout.

```python
def _fitted_size(image_path: Path, layout: Layout = THREE_UP):
    ...
    shape = pixel_w / pixel_h
    width = layout.width_in
    height = width / shape
    if height > layout.max_height_in:
        height = layout.max_height_in
        width = height * shape
    return Inches(width), Inches(height)
```

`IMAGE_WIDTH_IN` and `IMAGE_MAX_HEIGHT_IN` become `THREE_UP.width_in` and
`THREE_UP.max_height_in`. **Keep the whole comment block above them**, moved to
`THREE_UP`. It records that there is no portrait photograph in any delivered
report, that the extra page was the trailing paragraph and not the portrait
insurance, and that 4.00 x 3.00 is the size his reports already use. That is
measured evidence and it must not be lost in the move.
`app/tests/test_photo_fits_the_page.py` imports both names and moves with them.

**`_fill_cell_image` passes the layout through:**

```python
def _fill_cell_image(cell, image_path: Path, layout: Layout = THREE_UP):
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    width, height = _fitted_size(image_path, layout)
    p.add_run().add_picture(str(image_path), width=width, height=height)
```

**`_trim_unused_rows` takes the layout.** Its docstring keeps the 61-photograph
and 11-photograph findings, which are the evidence it exists at all:

```python
def _trim_unused_rows(doc, photo_count: int, layout: Layout = THREE_UP) -> int:
    if not doc.tables:
        return 0
    last = doc.tables[-1]
    used = photo_count - (len(doc.tables) - 1) * layout.per_page
    keep = layout.rows_for(max(0, used))
    removed = 0
    for row in list(last.rows)[keep:]:
        row._tr.getparent().remove(row._tr)
        removed += 1
    return removed
```

**`build_photo_docx` gains one keyword argument and uses it for every count:**

```python
def build_photo_docx(manifest_path: Path, template_path: Path,
                     prepare=None, out_base: str = DEFAULT_OUTPUT_BASE,
                     entries=None, layout: Layout = THREE_UP) -> Path:
    ...
    needed = max(1, -(-len(photos) // layout.per_page))  # ceil
    _grow_tables(doc, needed)
    _shrink_tables(doc, needed)

    for i, entry in enumerate(photos):
        table = doc.tables[i // layout.per_page]
        img_row, img_col, cap_row, cap_col = layout.cells(i % layout.per_page)
        source = photos_dir / entry.get("folder", "") / entry["file"]
        _fill_cell_image(table.rows[img_row].cells[img_col],
                         prepare(source) if prepare else source, layout)
        _fill_cell_caption(table.rows[cap_row].cells[cap_col],
                           entry.get("caption", ""))
    ...
    _trim_unused_rows(doc, len(photos), layout)
    _drop_trailing_blank_paragraphs(doc)
```

`layout` defaults to `THREE_UP` so the command-line entry point, every existing
test and `app/server/main.py` all keep working untouched in this slice.

**The proof that three-up has not moved.** Build the same photographs before
and after and compare, rather than asserting shapes:

```python
def test_three_up_is_byte_for_byte_what_it_was(tmp_path):
    """The layout object must be a refactor and nothing else. Two builds of
    the same manifest already produce identical documents (see
    test_photo_pages.py), so a difference here is this slice's fault."""
    names = write_five_photos(tmp_path)
    m = write_manifest(tmp_path, names)
    first = build_photo_docx(m, TEMPLATE_DOCX)
    second = build_photo_docx(m, TEMPLATE_DOCX, layout=THREE_UP)
    assert docx_body(first) == docx_body(second)
```

`docx_body` is the existing helper pattern in `app/tests/test_photo_pages.py`
for comparing two built documents; reuse it rather than writing a second one.

Run: `cd app/tests && python3 -m pytest -q`
Expected: PASS, and the skip count is what it was before this slice.

```bash
git add app/engine/photo_pages.py app/server/main.py app/tests/
git commit -m "refactor: the engine carries a layout instead of a bare 3

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Slice 2: a page that holds six

**`app/templates/Photo six-up.docx` is already built and Spenser approved it in
Word on 2026-09-07.** It is Mark's own template with nothing changed but the
tables: same page, same margins, same styles, same `SUBJECT PHOTOGRAPHS`
heading, same page-break paragraphs, same section properties, still fourteen
tables. If it needs rebuilding, it is his `Photo.docx` with each table's grid
set to two columns of 4824 twips and its three rows replaced by six alternating
rows of 3744 and 662 twips.

**Its furniture gets pinned the way the three-up one is**, in
`app/tests/test_shipped_template.py`, which deliberately carries no skip marker
because the template ships inside the app and is the path that actually runs on
Mark's PC:

```python
SIX_UP_SHIPPED = Path(__file__).resolve().parents[1] / "templates" / "Photo six-up.docx"


def test_shipped_six_up_template_matches_the_measured_budget():
    """2.60in photo rows and 0.46in caption rows are not arbitrary. They are
    the vertical budget in docs/plans/2026-09-07-six-up-photo-pages.md, and
    changing either without redoing that arithmetic overflows the page."""
    d = Document(str(SIX_UP_SHIPPED))
    s = d.sections[0]
    assert round(Emu(s.page_width).inches, 1) == 8.5
    assert round(Emu(s.left_margin).inches, 1) == 0.9
    assert len(d.tables) == 14
    for t in d.tables:
        assert len(t.rows) == 6 and len(t.columns) == 2
        assert [round(Emu(c.width).inches, 2) for c in t.rows[0].cells] == [3.35, 3.35]
        assert row_heights(t) == [2.6, 0.46, 2.6, 0.46, 2.6, 0.46]
    assert d.paragraphs[0].text.strip() == "SUBJECT PHOTOGRAPHS"
    assert len(d.inline_shapes) == 0
```

`row_heights(t)` reads `w:trHeight` off each `w:trPr` and divides by 1440. Write
it once in this module and use it in both template tests.

**The build tests** go in a new `app/tests/test_six_up_pages.py`, built on the
synthetic-image helpers `app/tests/test_no_extra_page.py` already uses. These
prove page arithmetic and trimming, which synthetic images are valid evidence
for:

```python
import pytest
from photo_pages import SIX_UP, build_photo_docx

SIX_UP_TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "Photo six-up.docx"


@pytest.mark.parametrize("count,pages", [(1, 1), (6, 1), (7, 2), (12, 2), (13, 3)])
def test_six_photographs_fill_one_page(tmp_path, count, pages):
    out = build_photo_docx(a_job(tmp_path, count), SIX_UP_TEMPLATE, layout=SIX_UP)
    assert len(Document(str(out)).tables) == pages


@pytest.mark.parametrize("count,rows", [(1, 2), (2, 2), (3, 4), (4, 4), (5, 6), (6, 6)])
def test_the_last_page_keeps_whole_pairs(tmp_path, count, rows):
    out = build_photo_docx(a_job(tmp_path, count), SIX_UP_TEMPLATE, layout=SIX_UP)
    assert len(Document(str(out)).tables[-1].rows) == rows


def test_an_odd_photograph_leaves_exactly_one_empty_box(tmp_path):
    """Spenser chose this on 2026-09-07 over merging the last pair into one
    full-width cell. It is a decision, not a gap: a photograph that changes
    size according to how many there happen to be surprises somebody later."""
    out = build_photo_docx(a_job(tmp_path, 5), SIX_UP_TEMPLATE, layout=SIX_UP)
    last = Document(str(out)).tables[-1]
    empty = [c for r in last.rows for c in r.cells
             if not c.text.strip() and not c._tc.findall(".//" + qn("a:blip"))]
    assert len(empty) == 2      # the photograph's cell and its caption's cell
```

**The overflow edge gets a test rather than a comment.** Six three-line
captions overflow the page by 0.80in. That page does not exist in Mark's work,
where one caption in two hundred runs to three lines at this width, but the
engine must not pretend it cannot happen:

```python
def test_a_page_of_very_long_captions_does_not_silently_overflow(tmp_path):
    """The 0.40in of slack absorbs two three-line captions, not six. Synthetic
    captions on purpose: this proves one mechanic, whether the page overflows,
    and makes no claim about Mark's writing."""
    out = build_photo_docx(a_job(tmp_path, 6, caption="x " * 60),
                           SIX_UP_TEMPLATE, layout=SIX_UP)
    assert page_height_used(Document(str(out)), 0) <= 10.5
```

`page_height_used` sums each row's declared height against its content height
and adds the heading. If this test fails, **do not shrink the photographs to
make it pass.** Bring it to Spenser: the open question in this plan is what the
app should do about it, and it is not decided.

**The golden test builds Mason City both ways**, in
`app/tests/test_photo_pages_golden.py`, behind the existing
`has_golden_corpus` marker so a clone without the corpus skips rather than
lies. It asserts fifty photographs give seventeen three-up pages and nine
six-up pages, and that every caption survives into the six-up document in the
same order.

Run: `cd app/tests && python3 -m pytest -q`

```bash
git add "app/templates/Photo six-up.docx" app/tests/
git commit -m "feat: a photo page that holds six

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Slice 3: the manifest can hold the choice

**Three per page is the default and the absent key means three**, the same
answer `bands_on`, `is_cut` and `is_reviewed` give for a missing key. Every
manifest on Mark's disk therefore reads as three per page with nothing to
convert.

In `app/server/photos.py`, beside `BANDS_ON`:

```python
PHOTOS_PER_PAGE = "photos_per_page"


def photos_per_page(manifest: dict) -> int:
    """How many photographs this job puts on a page. Three unless it says six.

    Absent means three, so every manifest written before this existed reads as
    the layout Mark already has and nothing on disk needs converting.
    """
    return 6 if manifest.get(PHOTOS_PER_PAGE) == 6 else 3
```

In `_validate_manifest_shape`, beside the `bands_on` check at line 734:

```python
    if PHOTOS_PER_PAGE in manifest and manifest[PHOTOS_PER_PAGE] not in (3, 6):
        return "A job's 'photos_per_page' must be 3 or 6."
```

**The server picks the template and the layout from that one value**, so the
two can never disagree. In `app/server/main.py`, replacing the single
`DEFAULT_PHOTO_TEMPLATE`:

```python
TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def _template_and_layout(manifest: dict):
    """One value decides both, so a six-up layout can never be filled into a
    three-up template. RRF_PHOTO_TEMPLATE still overrides the file, because it
    is how a different template is tested, but it does not change the layout:
    the manifest is the only thing that says how a page is shaped.
    """
    from photo_pages import LAYOUTS
    layout = LAYOUTS[photos_routes.photos_per_page(manifest)]
    override = os.environ.get("RRF_PHOTO_TEMPLATE")
    return Path(override) if override else TEMPLATES_DIR / layout.template, layout
```

and at the build call site, `app/server/main.py:1115`:

```python
        template, layout = _template_and_layout(manifest)
        ...
                    out = build_photo_docx(manifest_file, template,
                                           prepare=bench.copy_for_document,
                                           out_base=out_base,
                                           entries=photos_routes.included(manifest),
                                           layout=layout)
```

**`photo_pages_per_table()` at `app/server/main.py:56` is deleted.** It was
built to serve this number to the browser, was never called, and does not need
to exist now: the browser already fetches the manifest and the manifest already
carries the answer. Adding an endpoint would be a third place the layout lives.

**The manifest route normalises the value on the way out** so the browser never
has to know that an absent key means three. In `app/server/photos.py:811`:

```python
@router.get("/api/jobs/{name}/manifest")
def get_manifest(name: str):
    """The manifest, with photos_per_page always present and always 3 or 6.

    Normalised here rather than on disk. Nothing is written: a job that has
    never chosen still has no key in its file, which is what makes every
    manifest written before this feature read correctly. The browser gets a
    straight answer instead of repeating the default rule in JavaScript,
    which is how PhotosScreen.jsx came to hold its own `/ 3` in the first
    place.
    """
    manifest = load_manifest(_job_or_404(name))
    return {**manifest, PHOTOS_PER_PAGE: photos_per_page(manifest)}
```

Check `put_manifest` round-trips cleanly after this: the browser now sends back
a manifest carrying an explicit `photos_per_page`, which `_validate_manifest_shape`
accepts because 3 and 6 are both legal. A job that never touches the toggle
gains the key in its file the first time anything else is saved, and that is
harmless because 3 is what absent already meant.

**The tests**, in `app/tests/test_photos_api.py`:

```python
def test_a_manifest_without_the_key_is_three_per_page():
    assert photos.photos_per_page({"photos": []}) == 3


@pytest.mark.parametrize("bad", [0, 1, 2, 4, 5, 7, "6", True, None])
def test_only_three_or_six_may_be_written(client, job, bad):
    r = client.put(f"/api/jobs/{job}/manifest",
                   json={"photos": [], "photos_per_page": bad})
    assert r.status_code == 400
    assert "must be 3 or 6" in r.json()["detail"]


def test_the_override_changes_the_file_but_never_the_layout(monkeypatch, tmp_path):
    """RRF_PHOTO_TEMPLATE is how a different template is tested. It must not
    be able to put six-up cells into a three-up template."""
    monkeypatch.setenv("RRF_PHOTO_TEMPLATE", str(tmp_path / "whatever.docx"))
    _, layout = main._template_and_layout({"photos": [], "photos_per_page": 6})
    assert layout.per_page == 6
```

Note `True` in the bad-value list: `True == 1` in Python but is not 3 or 6, and
`isinstance(True, int)` is true, so a bool must be refused by the `in (3, 6)`
check rather than slipping through a type test.

Run: `cd app/tests && python3 -m pytest -q`

```bash
git add app/server/photos.py app/server/main.py app/tests/
git commit -m "feat: a job remembers how many photographs go on a page

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Slice 4: the toggle on the screen

**The toggle goes on the Photos title row**, using the `.toggle` control at
`app/web/src/brand.css:367` that the caption chooser already uses. No new
control and no new CSS beyond placement.

In `app/web/src/api.js`, beside the existing manifest calls:

```javascript
export const setPhotosPerPage = (name, manifest, perPage) =>
  fetch(`/api/jobs/${encodeURIComponent(name)}/manifest`, {
    method: "PUT", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...manifest, photos_per_page: perPage }),
  }).then(j);
```

It takes the manifest it is amending rather than fetching one, so it cannot
race a caption edit. The screen already holds the manifest in state, which is
how `putManifest` at `app/web/src/api.js:22` already works.

In `app/web/src/screens/PhotosScreen.jsx`, **delete line 336** and read the
number the server already normalised, with no default rule in JavaScript:

```javascript
  const perPage = manifest.photos_per_page;
  const pagesIn = Math.max(1, Math.ceil(inPhotos.length / perPage));
```

and on the title row, beside `<h1>Photos</h1>`:

```jsx
<div className="toggle layout-toggle">
  {[3, 6].map((n) => (
    <button key={n} className={perPage === n ? "on" : ""}
            disabled={!!busy}
            onClick={() => onPerPage(n)}>
      <span className="toggle-label">{n === 3 ? "Three per page" : "Six per page"}</span>
    </button>
  ))}
</div>
```

**The `page-preview` grid at line 864 follows it.** Today it is one photo cell
beside one caption cell. At six per page it is two photo cells above two
caption cells, because that grid's own comment promises it is drawn "exactly
the way photo_pages.py builds the real thing" and a promise like that has to
stay true.

**The tests**, in `app/web/src/screens/PhotosScreen.test.jsx`:

```javascript
it("shows Three per page for a job that has never chosen", () => {
  render(<PhotosScreen {...props({ manifest: manifest({ photos: six() }) })} />);
  expect(screen.getByRole("button", { name: /three per page/i }))
    .toHaveClass("on");
});

it("halves the page count when six is chosen", () => {
  const m = manifest({ photos: twelve(), photos_per_page: 6 });
  render(<PhotosScreen {...props({ manifest: m })} />);
  expect(screen.getByText(/about 2 pages/)).toBeInTheDocument();
});

it("leaves the tiles, the dots and the drag order alone", () => {
  // The toggle changes what Build makes. It must not touch the list.
  const before = tileOrder(render(<PhotosScreen {...props({ manifest: m3 })} />));
  const after = tileOrder(render(<PhotosScreen {...props({ manifest: m6 })} />));
  expect(after).toEqual(before);
});
```

Run: `cd app/web && npm test`
Then the whole Python suite again, because `test_ui_suite.py` runs the browser
tests from the Python side.

```bash
git add app/web/src/ app/tests/
git commit -m "feat: Mark picks three or six from the Photos screen

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Open, and not decided

**Six three-line captions on one page overflows by 0.80in.** The 0.40in of
slack absorbs two, not six. That page does not exist in Mark's work: one
caption in two hundred runs to three lines at this width, and the worst page
the corpus can produce fits with the full 0.40in spare. The three-up template
is worse on this axis today, where 19% of captions run to three or four lines.
Slice 2 makes it visible as a failing test rather than a silent overflow.
**What the app should do about it is Spenser's to decide, and shrinking the
photographs to dodge it is not the answer.**

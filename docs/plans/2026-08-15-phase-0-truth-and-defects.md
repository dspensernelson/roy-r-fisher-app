# Phase 0: Truth and Defects Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task if those skills are installed. If they are not, execute the tasks in order exactly as written; the plan is complete without them. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the five known defects in the app and make its stated facts true, so the working branch tells no lies before new capability lands on it.

**Architecture:** No new architecture. Five fixes inside existing modules (`settings.py`, `photos.py`, `readiness_scan.py`, `scan.py`), four new self-contained test files, one pinned requirements file, one README correction, and one screen change (Task 7), which carries this phase's goal conversation, its row-by-row mapping review, and its small screen stop.

**Tech Stack:** Python 3.9+, FastAPI, python-docx, Pillow, pytest. No new dependencies.

## Global Constraints

- Read `HOW-WE-WORK.md` and `docs/plans/2026-08-15-migration-roadmap.md` before starting. They govern.
- Python 3.9 compatible: no `int | None` unions, no `match` statements. `Optional[int]` style only.
- No em dashes anywhere: code, comments, docs, test names. Hyphens instead.
- Never touch `Report Examples/` (outside this repo) and never copy client material in.
- Never print, log, or move a real key. Tests use fake keys only.
- Work on a branch named `phase-0-truth-and-defects`, created from the current working branch. Commits on this branch are recovery checkpoints, allowed because Spenser approved this plan. Nothing is pushed, merged, or treated as accepted without his yes.
- Run commands from the repo root. The test suite runs with: `python3 -m pytest app/tests -q`
- The suite must end green (passes plus skips, zero failures) after every task.

---

### Task 1: The key file's export-form bug

An old launcher wrote the key as `export ANTHROPIC_API_KEY=...`. The reader (`stored_key`) accepts that form, but `save_key` and `remove_key` filter lines with `line.startswith("ANTHROPIC_API_KEY=")`, which does not match it. So a save appends a second key line while the old `export` line survives, and on the next start the old key wins (the screen shows the new last-four in the running process, because `save_key` also sets the live environment variable). Remove is a permanent no-op against that line. This was confirmed by execution, not just reading.

**Files:**
- Modify: `app/server/settings.py:120-128` (`save_key`, `remove_key`; add one helper above them)
- Test: `app/tests/test_settings.py` (append two tests)

**Interfaces:**
- Consumes: `settings.stored_key()`, `settings._lines()`, `settings._write()`, `settings.KEY_NAME` as they exist today.
- Produces: `settings._is_key_line(line: str) -> bool`, module-private. `save_key` and `remove_key` keep their exact signatures and behavior contracts.

- [ ] **Step 1: Write the two failing tests**

Append to `app/tests/test_settings.py` (it already has `import settings` and uses `monkeypatch`; match its style):

```python
def test_save_key_replaces_an_export_form_line(tmp_path, monkeypatch):
    key_file = tmp_path / "key.env"
    key_file.write_text("export ANTHROPIC_API_KEY=OLDKEY\n")
    monkeypatch.setenv("RRF_KEY_FILE", str(key_file))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    settings.save_key("NEWKEY")
    # Simulate the next start: the live env var save_key sets is gone.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert settings.stored_key() == "NEWKEY"
    assert "OLDKEY" not in key_file.read_text()


def test_remove_key_removes_an_export_form_line(tmp_path, monkeypatch):
    key_file = tmp_path / "key.env"
    key_file.write_text("export ANTHROPIC_API_KEY=OLDKEY\nOTHER=keep me\n")
    monkeypatch.setenv("RRF_KEY_FILE", str(key_file))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    settings.remove_key()
    assert settings.stored_key() == ""
    assert "OTHER=keep me" in key_file.read_text()
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 -m pytest app/tests/test_settings.py -q -k export_form`
Expected: 2 FAILED. The save test fails on `stored_key() == "NEWKEY"` (returns `OLDKEY`), the remove test on `stored_key() == ""`.

- [ ] **Step 3: Implement the fix**

In `app/server/settings.py`, add this helper directly above `save_key`, and change both functions' filters to use it:

```python
def _is_key_line(line: str) -> bool:
    """True when this line sets the key in any form stored_key accepts.

    save and remove must recognise every form stored_key does. Before this
    helper they matched only `ANTHROPIC_API_KEY=...`, so an old
    `export ANTHROPIC_API_KEY=...` line survived a save, and on the next
    start the old key won while the screen showed the new key's last four.
    """
    text = line.strip()
    if text.startswith("export "):
        text = text[len("export "):].lstrip()
    name, sep, _ = text.partition("=")
    return bool(sep) and name.strip() == KEY_NAME


def save_key(key: str) -> None:
    kept = [line for line in _lines() if not _is_key_line(line)]
    _write(kept + [f"{KEY_NAME}={key}"])
    os.environ[KEY_NAME] = key          # live, so nothing needs restarting


def remove_key() -> None:
    _write([line for line in _lines() if not _is_key_line(line)])
    os.environ.pop(KEY_NAME, None)
```

- [ ] **Step 4: Run the settings tests, then the whole suite**

Run: `python3 -m pytest app/tests/test_settings.py -q` then `python3 -m pytest app/tests -q`
Expected: all pass (skips are fine), zero failures.

- [ ] **Step 5: Commit**

```bash
git add app/server/settings.py app/tests/test_settings.py
git commit -m "fix: save and remove now match every key-line form stored_key reads"
```

---

### Task 2: The shipped template gets its first tests

Every build test points at the private corpus copy of `Photo.docx` and skips on machines without it. The copy at `app/templates/Photo.docx`, the one that will actually run on Mark's PC, is opened by no test at all. These tests must NOT use a skip marker: the shipped template is committed and always present.

**Files:**
- Create: `app/tests/test_shipped_template.py`

**Interfaces:**
- Consumes: `photo_pages.build_photo_docx(manifest_path, template_path) -> Path` from `app/engine/photo_pages.py`.
- Produces: nothing other tasks use.

- [ ] **Step 1: Write the test file**

Create `app/tests/test_shipped_template.py` with exactly this content:

```python
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
```

- [ ] **Step 2: Run it, then the whole suite**

Run: `python3 -m pytest app/tests/test_shipped_template.py -v`
Expected: 2 PASSED, 0 skipped. If the furniture test fails, STOP and report to Spenser: it means the shipped template differs from the measured contract, which is a finding, not a test to loosen.
Then run: `python3 -m pytest app/tests -q`
Expected: green, zero failures.

- [ ] **Step 3: Commit**

```bash
git add app/tests/test_shipped_template.py
git commit -m "test: the shipped Photo.docx is finally under test"
```

---

### Task 3: A corrupt manifest is a 400, not a crash

`photos._set_cut` and `photos.clear_captions` already catch bad JSON and return 400. `photos.load_manifest` does not, so `GET /api/jobs/{name}/manifest` and `POST /api/jobs/{name}/build` return a raw 500 on a malformed `photo-manifest.json`. A manifest whose top level is a JSON list also crashes with `AttributeError` before any validation runs. The file is hand-editable by design, so bad JSON is an expected condition and deserves a plain answer.

**Files:**
- Modify: `app/server/photos.py:104-128` (`load_manifest`, the file-reading branch only)
- Create: `app/tests/test_manifest_errors.py`

**Interfaces:**
- Consumes: `photos.load_manifest(job: Path) -> dict`, `photos.manifest_path(job)`.
- Produces: `load_manifest` now raises `fastapi.HTTPException(status_code=400)` on malformed JSON or a non-object top level. Its two callers (`photos.py` GET manifest, `main.py` build) inherit the 400 via FastAPI's exception handling; the tests here prove the function contract, not the routes. Other failure kinds (permissions, I/O) are out of scope and still raise.

- [ ] **Step 1: Write the failing tests**

Create `app/tests/test_manifest_errors.py`:

```python
"""photo-manifest.json is hand-editable by design, so a broken one is an
expected condition. The answer is a 400 that names the file, never a 500."""
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import photos  # noqa: E402


def _job_with_manifest_text(tmp_path, text):
    (tmp_path / "Photos").mkdir()
    (tmp_path / "Photos" / "photo-manifest.json").write_text(text)
    return tmp_path


def test_garbage_manifest_is_a_400_not_a_crash(tmp_path):
    job = _job_with_manifest_text(tmp_path, "{not json")
    with pytest.raises(HTTPException) as err:
        photos.load_manifest(job)
    assert err.value.status_code == 400
    assert "photo-manifest.json" in err.value.detail


def test_list_shaped_manifest_is_a_400_not_a_crash(tmp_path):
    job = _job_with_manifest_text(tmp_path, "[1, 2, 3]")
    with pytest.raises(HTTPException) as err:
        photos.load_manifest(job)
    assert err.value.status_code == 400
    assert "photo-manifest.json" in err.value.detail
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 -m pytest app/tests/test_manifest_errors.py -v`
Expected: 2 FAILED. The first with `json.decoder.JSONDecodeError`, the second with `AttributeError` (or a later crash), neither an `HTTPException`.

- [ ] **Step 3: Implement the fix**

In `app/server/photos.py::load_manifest`, the current reading branch is:

```python
    p = manifest_path(job)
    if p.is_file():
        manifest = json.loads(p.read_text())
```

Replace that branch with:

```python
    p = manifest_path(job)
    if p.is_file():
        # Hand-editable by design, so broken JSON is an expected condition,
        # not a crash. Same answer _set_cut and clear_captions already give.
        try:
            manifest = json.loads(p.read_text())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="photo-manifest.json is not valid JSON. "
                       "Fix the file or delete it and try again.")
        if not isinstance(manifest, dict):
            raise HTTPException(
                status_code=400,
                detail="photo-manifest.json should be a JSON object, "
                       "not a list or a bare value.")
```

`HTTPException` is already imported at the top of `photos.py`. Change nothing else in the function.

- [ ] **Step 4: Run the new tests, then the whole suite**

Run: `python3 -m pytest app/tests/test_manifest_errors.py -v` then `python3 -m pytest app/tests -q`
Expected: 2 PASSED; suite green.

- [ ] **Step 5: Commit**

```bash
git add app/server/photos.py app/tests/test_manifest_errors.py
git commit -m "fix: load_manifest answers 400 on a malformed manifest instead of crashing"
```

---

### Task 4: The readiness scan stops counting its own thumbnails

`app/engine/readiness_scan.py::_index` walks the whole job with `rglob("*")`. The app's thumbnail cache lives at `Photos/.rrf-thumbs/<name>.jpg`, so every cached thumbnail has a `.jpg` suffix and a parent containing "photos", and counts toward `photos.usable` and `photos.captioned`. The app is counting its own exhaust as arrived material.

**Files:**
- Modify: `app/engine/readiness_scan.py:46-48` (`_index`)
- Create: `app/tests/test_scan_excludes_thumbs.py`

**Interfaces:**
- Consumes: `readiness_scan.scan_job(job) -> dict` with `result["photos"]["usable"]`.
- Produces: `_index` no longer returns anything from the thumbnail cache. Signature unchanged. The mechanism is stated once, in Step 3, and not restated here.

- [ ] **Step 1: Write the failing test**

Create `app/tests/test_scan_excludes_thumbs.py`:

```python
"""The thumbnail cache is the app's own exhaust. It must never count as
arrived photos, or a job with one photo and one thumbnail reads as two."""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from readiness_scan import scan_job  # noqa: E402


def test_thumbnail_cache_never_counts_as_photos(tmp_path):
    photos = tmp_path / "Photos"
    (photos / ".rrf-thumbs").mkdir(parents=True)
    Image.new("RGB", (40, 30), (10, 80, 90)).save(photos / "IMG_5100.jpg")
    Image.new("RGB", (40, 30), (10, 80, 90)).save(
        photos / ".rrf-thumbs" / "IMG_5100.jpg.jpg")
    result = scan_job(tmp_path)
    assert result["photos"]["usable"] == 1
```

If `scan_job` fails because the bare folder is missing something it expects, create the empty folder the error names inside `tmp_path` and re-run. Do not weaken the assertion.

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest app/tests/test_scan_excludes_thumbs.py -v`
Expected: FAIL with `usable == 2`.

- [ ] **Step 3: Implement the fix**

In `app/engine/readiness_scan.py`, `_index` currently returns:

```python
    return [p for p in job.rglob("*")
            if p.is_file() and p.name not in (".DS_Store", "Thumbs.db", "desktop.ini")
            and not any(x in str(p.parent).lower() for x in EXCLUDE)]
```

Change it to:

```python
    return [p for p in job.rglob("*")
            if p.is_file() and p.name not in (".DS_Store", "Thumbs.db", "desktop.ini")
            and ".rrf-thumbs" not in p.parts
            and not any(x in str(p.parent).lower() for x in EXCLUDE)]
```

- [ ] **Step 4: Run the new test, then the whole suite**

Run: `python3 -m pytest app/tests/test_scan_excludes_thumbs.py -v` then `python3 -m pytest app/tests -q`
Expected: PASS; suite green.

- [ ] **Step 5: Commit**

```bash
git add app/engine/readiness_scan.py app/tests/test_scan_excludes_thumbs.py
git commit -m "fix: readiness scan no longer counts the thumbnail cache as photos"
```

---

### Task 5: Pin the requirements

`app/server/requirements.txt` is eleven bare names. These are the versions installed on Spenser's Mac as of 2026-08-15; pinning them means a future install on any machine gets the same combination of versions the current full suite was run green against.

**Files:**
- Modify: `app/server/requirements.txt` (full rewrite)

**Interfaces:**
- Consumes: nothing.
- Produces: a pinned requirements file later packaging work will rely on.

- [ ] **Step 1: Rewrite the file**

Replace the entire content of `app/server/requirements.txt` with:

```
# Pinned 2026-08-15 to the versions the test suite actually runs against
# on the development Mac. Top-level pins only; transitive dependencies
# float, and a fully frozen lock is a packaging-phase job. Change a pin
# only with the suite green after.
fastapi==0.128.8
uvicorn[standard]==0.39.0
python-multipart==0.0.20
pillow==11.3.0
pillow-heif==1.1.1
anthropic==0.121.0
pydantic==2.13.4
python-docx==1.2.0
pypdf==6.14.2

# Test-only.
pytest==8.4.2
httpx==0.28.1
```

- [ ] **Step 2: Verify the pins match reality**

Run: `python3 -m pip freeze | grep -iE "^(fastapi|uvicorn|python-multipart|pillow|pillow_heif|anthropic|pydantic|python-docx|pypdf|pytest|httpx)="`
Expected: every version in the file appears in the output (pip prints `pillow_heif`; the install name `pillow-heif` in the file is correct).

- [ ] **Step 3: Prove the file installs clean and the suite passes on it**

Build a fresh environment in the session scratchpad (never inside the repo) and run the suite from it:

```bash
python3 -m venv "$SCRATCHPAD/pin-check" && "$SCRATCHPAD/pin-check/bin/pip" install -q -r app/server/requirements.txt && "$SCRATCHPAD/pin-check/bin/python" -m pytest app/tests -q
```

(`$SCRATCHPAD` is your session's scratchpad directory; substitute its real path.)
Expected: install succeeds and the suite is green, zero failures. This proves the pinned file reproduces a working environment on this platform; Windows installation is proven later, in the Phase 1 acceptance slice.

- [ ] **Step 4: Commit**

```bash
git add app/server/requirements.txt
git commit -m "chore: pin requirements to the tested versions"
```

---

### Task 6: The README stops lying twice

Two stated facts are false. "109 tests pass" is stale; the suite collects 285. And "nothing in it reads anything outside itself" is contradicted twice in code: `app/server/demo.py` computes the repo root above `app/`, and one styling test reads `brand/`.

**Files:**
- Modify: `README.md` (two lines)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing.

- [ ] **Step 1: Measure the real test numbers**

This step runs only after every test file Phase 0 adds is in place, so the number the README states is the number the finished slice actually has. If any Phase 0 task is still to come, the count measured now is not the count to write; measure again at the end of the slice and correct the line before the slice closes.

Run: `python3 -m pytest app/tests -q | tail -2`
Note the passed and skipped counts from the summary line. The number to write is passed plus skipped. Use that measured number. This plan states no test count anywhere, on purpose: a number written into a plan is stale the moment a test is added, which is the defect this task exists to fix.

- [ ] **Step 2: Correct the two lines**

In `README.md`:

Replace the line `109 tests pass.` with the sentence below, substituting the measured total for `<total>`:

```
<total> tests; the ones that need Mark's private material skip on machines without it.
```

In the root table, replace the `app/` row text `Stands on its own; nothing in it reads anything outside itself` with:

```
The code reads no project files outside app/. At run time it also uses the settings and key files in the home folder and the jobs folder Mark points it at. Two dev tools reach wider: demo reset finds the repo root, and one styling test reads brand/
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README states the measured test count and the two outside readers"
```

---

### Task 7: The readiness panel stops discarding and stops overclaiming

> **BLOCKED.** This task may not start. It is blocked on Spenser's row-by-row
> review of the 19-row `REQUIREMENTS` mapping in
> `app/engine/readiness_scan.py`, and on his answers to the two open questions
> named below. The 19 rows were put to him in chat on 2026-08-15 and no
> verdicts have been recorded yet. No code, test, or screen change in this
> task may be written before every row has a verdict. Nothing in this task
> may be inferred, guessed, or filled in on his behalf.

Today `scan.folder_rows` builds rows only for the eight predefined folders in `jobs.MARK_FOLDERS` and silently drops any requirement whose folder is not among them (the `continue` at `app/server/scan.py:43-44` discards the Improvements and Transcript information checks entirely). The screen then prints "Nothing this report needs comes from here" on empty rows (`JobHome.jsx:52`), a claim nothing has proven. Required behavior (Spenser, 2026-08-15): rows come from the folders actually on disk, by exact name; no requirement is ever silently discarded; no unproven claim is shown; folders without a reviewed mapping show only observable facts (name, file count); and the mapping table is reviewed row by row before the app may say "Has" or "Still needs" from it.

**Two further requirements, both unresolved and both blocking:**

1. **A requirement the chosen report shape does not need is not a thing the
   job is missing.** Before the screen may say "Still needs" about any
   requirement, it must account for whether the selected report shape
   actually calls for it. A rent roll is not missing from an appraisal whose
   shape has no Income Approach. The applicability rules do not exist yet and
   this plan does not invent them: which shapes need which requirements is
   Spenser's to state, and the row-by-row review is where it gets stated. If
   the rules are not settled, "Still needs" is not available and the row shows
   only observable facts.

2. **File detection must use exact folder identity, not substring matching
   across the full path.** Today `readiness_scan.in_folder` tests
   `folder.lower() in str(p.parent).lower()`, which matches anywhere in the
   whole path. A folder named `Maps` therefore also matches a job whose name
   contains "maps", and `Comps` matches a path containing "comps" at any
   depth. Detection must instead resolve the named folder as an exact
   top-level folder of the job, and count files inside it including its
   legitimate descendants. A file two levels down inside `Maps/` still belongs
   to `Maps`. A file in an unrelated folder whose path happens to contain the
   word does not.

**Files:**
- Modify: `app/server/scan.py:33-57` (`folder_rows`)
- Modify: `app/server/main.py:325-328` (the scan route)
- Modify: `app/engine/readiness_scan.py:15-35` (`REQUIREMENTS`, only as the review directs)
- Modify: `app/web/src/screens/JobHome.jsx:43-55` (the folder band)
- Test: Create `app/tests/test_scan_rows_truth.py`

**Interfaces:**
- Consumes: `readiness_scan.scan_job(job)` unchanged; `readiness_scan.REQUIREMENTS` as reviewed.
- Produces: `scan.folder_rows(job: Path) -> dict` now returns `{"folders": [row, ...], "unplaced": [{"note": str, "expected_folder": str}, ...]}` instead of a bare list. Row shape (`folder`, `count`, `here`, `needs`, `status`) is unchanged. The route returns that dict directly, so the response gains an `unplaced` key.

- [ ] **Step 1: Goal conversation and the row-by-row mapping review. STOP here.**

This is a gate, not a formality. Post in chat to Spenser: the one-sentence goal ("Make the readiness panel show only what is true: every real folder, every requirement, no unproven claims"), then every row of `REQUIREMENTS` from `app/engine/readiness_scan.py`, one line each, showing section, folder, patterns, and note. Ask for a verdict per row: keep, correct (with his wording), or remove. Do not proceed until every row has a verdict. Then edit `REQUIREMENTS` to match the verdicts exactly and add a comment above the table: `# Reviewed row by row by Spenser on <date of review>.` Surviving rows are the only mapping the app may use to say "Has" or "Still needs".

**Status: the 19 rows were put to Spenser in chat on 2026-08-15. No verdicts have been recorded. This step is open and the task is blocked behind it.**

The same review must also settle the two requirements named in this task's header. On report-shape applicability, ask him which requirements each report shape actually needs, and record his answer as his words. Do not draft a shape-to-requirement mapping for him to approve: an invented mapping that he skims and waves through is exactly the confident wrong answer this app must never produce. If he does not settle it, the screen says nothing about "Still needs" and shows observable facts only.

- [ ] **Step 2: Write the failing tests**

Create `app/tests/test_scan_rows_truth.py`:

```python
"""Two truths the readiness panel must keep: every folder on disk appears
by its exact name, and no requirement is ever silently discarded."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
import scan  # noqa: E402
import readiness_scan  # noqa: E402


def test_every_disk_folder_appears_by_exact_name(tmp_path):
    (tmp_path / "Legal").mkdir()
    (tmp_path / "Legal" / "easement.pdf").write_bytes(b"x")
    (tmp_path / "Photos").mkdir()
    result = scan.folder_rows(tmp_path)
    names = [r["folder"] for r in result["folders"]]
    assert "Legal" in names and "Photos" in names
    legal = next(r for r in result["folders"] if r["folder"] == "Legal")
    assert legal["count"] == 1
    # No reviewed mapping names Legal, so it may claim nothing.
    assert legal["here"] == [] and legal["needs"] == []


def test_no_pattern_requirement_is_ever_discarded(tmp_path):
    # A job with only a Photos folder: most requirements have nowhere to
    # land. Every one of them must still come back, placed or unplaced.
    (tmp_path / "Photos").mkdir()
    result = scan.folder_rows(tmp_path)
    shown = set()
    for row in result["folders"]:
        shown.update(row["here"])
        shown.update(row["needs"])
    shown.update(u["note"] for u in result["unplaced"])
    expected = {note for (_s, _f, pats, note)
                in readiness_scan.REQUIREMENTS if pats}
    assert expected <= shown
```

- [ ] **Step 3: Run them to verify they fail**

Run: `python3 -m pytest app/tests/test_scan_rows_truth.py -v`
Expected: 2 FAILED. Today `folder_rows` returns a list, so both tests fail on the return shape before reaching the real assertions.

- [ ] **Step 4: Rewrite `folder_rows`**

Replace the body of `folder_rows` in `app/server/scan.py` with:

```python
def folder_rows(job: Path) -> dict:
    """Every folder actually on disk, by exact name, plus every requirement
    that could not be placed on one of them.

    Nothing is discarded: a requirement either lands on a folder row or
    comes back in unplaced. A folder with no reviewed mapping shows only
    what is observable, its name and file count, and claims nothing.
    """
    result = scan_job(job)
    on_disk = [p.name for p in sorted(job.iterdir())
               if p.is_dir() and not p.name.startswith(".")]
    ordered = ([n for n in jobs.MARK_FOLDERS if n in on_disk]
               + [n for n in on_disk if n not in jobs.MARK_FOLDERS])
    rows = {name: {"folder": name, "count": _count_files(job / name),
                   "here": [], "needs": []}
            for name in ordered}

    unplaced = []
    for checks in result["sections"].values():
        for check in checks:
            placed = False
            for folder in check["folder"].split("|"):
                row = rows.get(folder)
                if row is None:
                    continue
                bucket = "here" if check["hits"] else "needs"
                if check["note"] not in row[bucket]:
                    row[bucket].append(check["note"])
                placed = True
            if not placed:
                unplaced.append({"note": check["note"],
                                 "expected_folder": check["folder"]})

    for folder, (label, count_of) in COUNTED.items():
        row = rows.get(folder)
        if row is None:
            continue
        row["here" if count_of(result) else "needs"].append(label)

    for row in rows.values():
        row["status"] = "waiting" if row["needs"] else "ready"
    return {"folders": [rows[n] for n in ordered], "unplaced": unplaced}
```

In `app/server/main.py`, the scan route currently returns `{"folders": scan.folder_rows(...)}`. Change it to return the dict directly:

```python
    @app.get("/api/jobs/{name}/scan")
    def scan_job_folders(name: str):
        # folder_rows already returns {"folders": ..., "unplaced": ...}
        return scan.folder_rows(photos_routes._job_or_404(name))
```

- [ ] **Step 5: Run the new tests, then the whole suite**

Run: `python3 -m pytest app/tests/test_scan_rows_truth.py -v` then `python3 -m pytest app/tests -q`
Expected: the new tests pass. If an existing test fails because it pinned the old behavior (rows for folders not on disk, requirements silently dropped, the bare-list return shape), update that test to the new contract; those tests were pinning the defect. Any other failure is a real break: stop and fix it.

- [ ] **Step 6: Change the screen**

In `app/web/src/screens/JobHome.jsx`:

First, keep both pieces of the scan result. Change the load line:

```jsx
      .then(([d, s]) => { setDetail(d); setFolders(s.folders); setUnplaced(s.unplaced); })
```

and add the state hook beside the others:

```jsx
  const [unplaced, setUnplaced] = useState([]);
```

Second, delete the unproven claim. Remove these three lines entirely:

```jsx
              {f.here.length === 0 && f.needs.length === 0 && (
                <div className="line quiet">Nothing this report needs comes from here</div>
              )}
```

A row with nothing to say shows its name and count, which are observable, and says nothing else.

Third, directly after the `{(folders || []).map(...)}` block's closing, add the unplaced block:

```jsx
          {(unplaced || []).length > 0 && (
            <div className="folder">
              <div className="top">
                <span className="name">Also checked for, no folder to look in</span>
              </div>
              {unplaced.map((u) => (
                <div className="line needs" key={u.note}>
                  {u.note} (looks in a folder named {u.expected_folder.split("|").join(" or ")})
                </div>
              ))}
            </div>
          )}
```

Every word there is observable: what the scan looks for and where it looks. No claim about what the report needs.

- [ ] **Step 7: Rebuild the web bundle and look at it**

Run: `cd app/web && npm run build && cd ../..`
Then start the app (`python3 app/run_app.py`), open a demo job, and check with your own eyes: every real folder listed by exact name, no "Nothing this report needs comes from here" anywhere, and the unplaced block present when the job lacks an expected folder.

- [ ] **Step 8: Commit, then request the small screen stop**

```bash
git add app/server/scan.py app/server/main.py app/engine/readiness_scan.py app/web/src/screens/JobHome.jsx app/tests/test_scan_rows_truth.py
git commit -m "fix: readiness panel shows real folders, drops no requirement, claims nothing unproven"
```

Then STOP and ask Spenser to click through the job screen. This is the small screen stop; his notes fold into this task before the slice closes.

---

### Task 8: Close the slice

- [ ] **Step 1: Run the full suite one last time**

Every test file this phase adds must already be in place, Task 7's included. This is the last measurement of the phase and the one the README will state.

Run: `python3 -m pytest app/tests -q`
Expected: zero failures. Record the exact summary line, both the passed count and the skipped count.

- [ ] **Step 2: Make the README count match that result**

Task 6 corrects the README's test count partway through this phase, and every task after Task 6 adds more tests. So the sentence Task 6 wrote is stale by the time the phase closes. This step exists to catch that, and without it the phase ends having reintroduced the exact defect Task 6 was written to fix.

Open `README.md` and read the test-count sentence. The number in it must equal passed plus skipped from Step 1. If it does not, correct it now to the Step 1 numbers.

Then verify rather than assume. Run `python3 -m pytest app/tests -q` once more and check the sentence in the file against that summary line. The phase does not close on a README number nobody has just checked against a real suite result.

If the sentence changed, commit it:

```bash
git add README.md
git commit -m "docs: README states the final measured test count for the phase"
```

- [ ] **Step 3: Report to Spenser and stop**

Post in chat:

- the branch name
- every commit on this branch since its branch point, in order, each with its short hash and what it did. List what is actually there, however many that is. This plan states no commit count, because documentation checkpoints change it.
- the final test summary line from Step 1
- whether the README sentence needed correcting in Step 2, and what it says now
- the outcome of the Task 7 mapping review and the small screen stop
- anything found along the way that this plan did not predict

Nothing is pushed or merged; that is Spenser's call after review.

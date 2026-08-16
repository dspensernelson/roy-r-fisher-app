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

Every build test points at the private corpus copy of `Photo.docx` and skips on machines without it. The copy at `app/templates/Photo.docx`, the one that will actually run on the appraiser's PC, is opened by no test at all. These tests must NOT use a skip marker: the shipped template is committed and always present.

**Files:**
- Create: `app/tests/test_shipped_template.py`

**Interfaces:**
- Consumes: `photo_pages.build_photo_docx(manifest_path, template_path) -> Path` from `app/engine/photo_pages.py`.
- Produces: nothing other tasks use.

- [ ] **Step 1: Write the test file**

Create `app/tests/test_shipped_template.py` with exactly this content:

```python
"""The template that ships inside the app is the one the appraiser's PC will use.

Every other build test points at the private corpus copy, which a clone may
not have. These tests point at app/templates/Photo.docx, which is always
present, so the path that actually runs on the appraiser's machine is never the one
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
<total> tests; the ones that need the appraiser's private material skip on machines without it.
```

In the root table, replace the `app/` row text `Stands on its own; nothing in it reads anything outside itself` with:

```
The code reads no project files outside app/. At run time it also uses the settings and key files in the home folder and the jobs folder the appraiser points it at. Two dev tools reach wider: demo reset finds the repo root, and one styling test reads brand/
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README states the measured test count and the two outside readers"
```

---


### Task 7: Show every folder honestly, and let the appraiser say what a file is

Replaces the earlier Task 7, which was withdrawn by product review on 2026-08-16. The withdrawn version treated a likely filename as a requirement and mixed "a file is present" with "the information is usable". Nothing in this task reads `readiness_scan.REQUIREMENTS`, and the 19-row mapping review is no longer a gate on it. That table and its CLI stay exactly as they are, unused by the screen, waiting for the later information-needs slice.

**Goal:** Replace the eight guessed folder rows with every folder actually on disk, let the appraiser open any folder and see the files inside it, and let him confirm what a file is, with the app storing that answer outside his folders and never touching his files.

**Before.** the appraiser opens a job. He sees eight fixed rows. A folder he made himself is invisible. He cannot see a single filename. A row says "Has deed" because a file somewhere under a path containing "subject information" had "deed" in its name. He cannot correct any of it.

**After.** He sees "Typical folders" and "Other folders found", each folder by its exact name on disk with a file count. He clicks `Maps` and sees the files in it, including one in a subfolder, which says where it sits. Beside each file is a Classify action. He classifies `plat 2025 final.pdf` as "Plat map" and the row says so. If he renames that file in Explorer, the app says the source is gone rather than still claiming a plat map.

**Product decisions, settled 2026-08-16. Do not reopen these.**

1. The classification list is the nine options in Step 3, exactly. No Building sketch, no Flood map, no free text, nothing else in this slice.
2. Files sitting directly in the job folder appear under "Loose files in the job folder" and may be classified under the same rules as any other file.
3. Size and modification date are recorded when the appraiser confirms. If the source at that path later differs, the screen says it changed and stops presenting the classification as currently confirmed.
4. The words "Has" and "Still needs" appear nowhere in this slice. The screen may state what files were observed, what the appraiser classified, and whether a classified source is present, changed, or missing.
5. Classifications live outside the appraiser's folders, in the app-owned file named in Step 2. `photo-manifest.json` stays a narrow existing exception and that precedent is not widened.

**Files:**
- Create: `app/server/inventory.py`, `app/server/classify.py`
- Create: `app/tests/test_inventory.py`, `app/tests/test_classify.py`, `app/tests/test_file_safety.py`
- Modify: `app/server/main.py` (three new routes; delete the `/scan` route)
- Modify: `app/web/src/api.js`, `app/web/src/screens/JobHome.jsx`, `app/web/src/styles.css`
- Modify: `app/tests/test_scan.py` (delete the six `folder_rows` tests, keep the four engine and CLI tests)
- Delete: `app/server/scan.py`
- Unchanged: `app/engine/readiness_scan.py`

**File safety, the hard line.** The implementation may read directory names, filenames, relative paths, sizes, and modification dates. It may not open or read file contents, modify, rename, move, or delete a source file, create anything inside the appraiser's job folders, follow a symlink outside the job, or infer a classification from a filename. If `test_file_safety.py` fails, stop and report. It is never weakened.

- [ ] **Step 1: Inventory, tests first**

Create `app/tests/test_inventory.py`, then `app/server/inventory.py` to satisfy it.

Folder identity is exact. `inventory` calls `job.iterdir()`, keeps entries where `is_dir()` is true, and the folder's identity is that entry's exact `name`. There is no case folding, no substring test, and no path-string matching anywhere in the module. This is what replaces `readiness_scan.in_folder`'s `folder.lower() in str(p.parent).lower()`, which matched a job whose own path contained the folder's name.

Behavior per entry kind:

| Kind | Behavior |
|---|---|
| Nested file, `Maps/2025/plat.pdf` | Belongs to `Maps`. Reports `within` as `2025` |
| Hidden entry, name starts with `.` | Not listed. Same as `workspace.child_folder_names` already does |
| `.DS_Store`, `Thumbs.db`, `desktop.ini` | Not listed. Reuse `workspace.NOISE` |
| `.rrf-thumbs` | Not listed, both as hidden and by name |
| `photo-manifest.json` | Listed. It is a real file in his folder |
| Symlink or shortcut, file or folder | Detected with `is_symlink()` **before** any traversal, listed by name with `kind` of `shortcut`, never followed, never traversed, no Classify action |
| Path resolving outside the job | Not listed. Reuse `photos._resolve_confined` |
| Loose file at the job root | Returned in `root_files` |
| Folder with many files | Count is always true; the list is capped at 200 with a truncation flag, copying `workspace.NAME_LIMIT` |
| Unreadable folder | Listed, flagged unreadable, never reported as empty |

Run: `python3 -m pytest app/tests/test_inventory.py -v`

- [ ] **Step 2: Classification storage, tests first**

Create `app/tests/test_classify.py`, then `app/server/classify.py`.

Storage is `~/.rrf-classifications.json`, overridable by `RRF_CLASSIFY_FILE` for tests, copying the pattern already proven by `RRF_KEY_FILE` and `RRF_SETTINGS_FILE`. It sits in the home folder because HOW-WE-WORK's Never list says app knowledge never goes into the appraiser's folders.

```json
{
  "jobs": {
    "/Users/mark/Jobs/DAVENPORT_215 E 37th Street - 2026": {
      "Maps/plat 2025 final.pdf": {
        "label": "Plat map",
        "confirmed_at": "2026-08-16",
        "size": 284113,
        "mtime": 1755300000.0
      }
    }
  }
}
```

The job key is the resolved absolute path of the job folder, the same keying `workspace.save_active_jobs` uses. The file key is the path relative to the job root in POSIX form, so one record works on both machines. Nothing is written into, renamed on, or read out of the appraiser's folders to make this work.

The write must be safe. A failed write may not destroy existing classifications, so write to a temporary file in the same folder and replace atomically. Updating one job preserves every other job and every unrelated file record in it, the way `workspace.save_folder` already leaves every other key alone.

Verdict on a classified file, computed by reading the directory only:

- `present`: the relative path exists and size and mtime match what was recorded
- `changed`: it exists but size or mtime differ
- `missing`: nothing is at that path

Run: `python3 -m pytest app/tests/test_classify.py -v`

- [ ] **Step 3: The approved classification registry**

Nine options, approved by Spenser on 2026-08-16, in `classify.py` as a module constant:

| Option | Why it is on the list |
|---|---|
| Engagement letter | Defines the assignment; Phase 4 reads it into the intake form |
| Deed | Standard intake document in every report shape in the corpus |
| Assessor or tax record | Same |
| Subject photograph | Photo pages are the only section that builds today |
| Plat map | First of the image-page family, the next section family to build |
| Neighborhood map | Same family |
| Aerial photo | Same family |
| Comparable sale document | The Sales approach needs these identified |
| Valuation workbook | Phase 1 reads the `.xlsm` for grids and needs it pointed at |

Anything outside this list is refused with a 400. No free text.

- [ ] **Step 4: API routes, tests first**

`GET /api/jobs/{name}/folders` returns:

```json
{
  "typical": [{"folder": "Maps", "count": 4, "unreadable": false,
               "truncated": false, "files": []}],
  "other": [],
  "root_files": [],
  "missing_classifications": []
}
```

A file entry:

```json
{"name": "plat 2025 final.pdf", "rel": "Maps/2025/plat 2025 final.pdf",
 "within": "2025", "kind": "file",
 "classification": {"label": "Plat map", "state": "present"}}
```

`classification` is `null` when unclassified. Files are returned inline: a job holds tens of files, and one request keeps rows from flickering as they open.

**A classified file is never silently dropped.** If its source is gone but its folder still exists, it appears in that folder's list with `kind` of `missing` and state `missing`. If its folder is gone too, it appears in `missing_classifications` so the record is always reachable and removable.

`PUT /api/jobs/{name}/classification`, body `{"file": "...", "label": "..."}`. Creates or replaces; Change classification is the same call with a different label. 400 on a label outside the registry. 404 when the file is not in the job's current inventory, so no record can exist for a file the app has not just observed.

`DELETE /api/jobs/{name}/classification`, body `{"file": "..."}`. Removes the app's record only. Touches nothing in the appraiser's folders. Works on a missing source, which is how he clears a stale record.

Both use `photos._job_or_404` unchanged.

Run: `python3 -m pytest app/tests/test_inventory.py app/tests/test_classify.py app/tests/test_file_safety.py -v`

- [ ] **Step 5: Delete the old screen scan path**

Delete `app/server/scan.py`, the `/api/jobs/{name}/scan` route in `main.py`, `scanJob` in `api.js`, and the six `folder_rows` tests in `test_scan.py`. Keep the four tests covering `readiness_scan` and its CLI.

Leaving a live endpoint that manufactures "Has" from filenames is how it comes back.

Run: `python3 -m pytest app/tests -q`. Expected green. A failure outside those six tests is a real break: stop and report.

- [ ] **Step 6: The screen, then rebuild**

In `JobHome.jsx`, the folder band becomes three sections: "Typical folders", "Other folders found", "Loose files in the job folder", plus a "Classified files whose source is missing" area when that list is not empty. Every folder shows its exact disk name and file count, collapsed, and expands to its file list. A nested file shows where it sits. A shortcut is named and marked, with no Classify action.

Delete the line "Nothing this report needs comes from here" and replace it with nothing. A row with nothing to say shows its name and count.

The words "Has" and "Still needs" appear nowhere.

Run: `cd app/web && npm run build && cd ../..`, then start the app and open a real demo job.

- [ ] **Step 7: The small screen stop**

Commit, then STOP and ask Spenser to click through. Report the branch, every new commit with its purpose, the focused test result, the full-suite result, the exact files changed, confirmation that his job files were byte-for-byte unchanged, the command to open the app, any difference between this plan and what was built, and anything still unproven.

Task 8 does not begin until he has reviewed the working screen.
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

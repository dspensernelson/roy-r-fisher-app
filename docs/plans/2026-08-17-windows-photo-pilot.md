# Windows Photo Pilot implementation plan

Written 2026-08-17 on branch `windows-photo-pilot`, cut from `main` at the
Phase 0 merge (`5b7ee7c`). Authorized by the roadmap decision of 2026-08-17,
"Mark receives an early Windows Photo Pilot, before the handoff bundle".

**Goal.** Mark receives a versioned Windows package that he unzips once,
launches with one double-click, points at his jobs folder, sets up guarded AI
captions, and uses to build Subject Photograph pages. No Python, no Node, no
Terminal, no development tools.

**What this is not.** Not the Phase 1 Windows Office proof: photo pages need
no Office at all, so nothing here says anything about Excel, Word automation,
or PDF through COM. Not the complete handoff through Phase 3. Not Phase 5
final packaging. Nothing in Description of Improvements.

## Global constraints

- `HOW-WE-WORK.md` governs. Its Never list has no judgement in it.
- Python 3.9 compatible source: no `int | None` unions, no `match`. Verified
  clean across `app/server`, `app/engine`, and `app/run_app.py` on 2026-08-17.
- No em dashes anywhere: code, comments, docs, UI copy, launcher text.
- Never write into `Report Examples/`. Never copy client material into the
  repo or into the package.
- Never print, log, or move a real key. Tests use fake keys only.
- The suite must end green after every task: `python3 -m pytest app/tests -q`
- Commits on this branch are recovery checkpoints. Nothing is pushed, opened
  as a pull request, or merged without Spenser's yes.

---

## 1. What currently works unchanged

Inspected on 2026-08-17 at `5b7ee7c`. None of this needs changing for the
pilot.

| Area | State | Evidence |
|---|---|---|
| Server and web on one port | `app/run_app.py` starts uvicorn on 127.0.0.1:8000 and `main.py` mounts `app/web/dist` at `/` | `main.py:517-542` |
| Jobs folder selection | Chosen on a screen, remembered in `~/.rrf-app.json` | `workspace.py:23,35-39` |
| Key entry and display | Saved to `~/.rrf-app.env`, last four only ever reaches the browser | `settings.py:97-101` |
| Key file robustness | Reads `export`, indented, and quoted forms; save and remove match all of them | `settings.py:62-79,120-143` |
| Photo manifest and cuts | Reversible cuts, hand-editable manifest, 400 on malformed JSON | `photos.py`, Phase 0 Task 3 |
| Photo document build | Real Word file from the shipped template | `photo_pages.build_photo_docx` |
| Non-overwrite output | Counts up until a free name is found; never returns an existing filename | `photo_pages.next_output_name:54-69` |
| Windows-safe naming | `WINDOWS_FORBIDDEN` strip already used for folder names | `jobs.py:52,59` |
| Home-folder paths | `Path.home()` on both platforms for key, settings, classifications | `settings.py:28`, `workspace.py:39`, `classify.py:45` |
| No Mac-only calls | No `subprocess`, `osascript`, or POSIX-only call anywhere in the app path | grep, 2026-08-17 |
| Demo reset already off | `demo.enabled()` gates the route; the button never renders unconfigured | `main.py:113-125` |

Two consequences worth stating. The non-overwrite machinery already exists,
so the filename work is a change of base name, not new safety. And every piece
of app-owned state already lives in the home folder, outside the package, so
versioned pilot updates preserve Mark's setup with no migration code.

## 2. What must change for the new output filename

Today `next_output_name` returns `Photo (RRF App).docx`, counting up to
`Photo (RRF App 2).docx` when taken. The pilot requires
`City_Address Photos (Complete).docx` with the same never-overwrite behavior.

Three changes:

1. **A shared filename sanitizer.** `jobs.py:52-61` already strips
   `WINDOWS_FORBIDDEN`, collapses whitespace, trims trailing dots and spaces,
   and caps length. That logic moves to one helper both the folder namer and
   the output namer call, so the two can never drift.
2. **`next_output_name` takes the base name.** Signature becomes
   `next_output_name(photos_dir, base)`. The counting loop is unchanged. The
   existing default stays as the fallback base only where the plan below says
   a fallback is allowed.
3. **A confirmed source of city and address.** This is the open question in
   Section 14. The rule is fixed regardless of the answer: neither value is
   ever guessed, and the build refuses rather than invents.

**What is not changed.** The counting loop, the confinement checks, the
template, and the layout engine. No existing generated output is touched.

## 3. AI guardrails: which exist, which are missing

Measured against the eleven locked guardrails.

**Already in place, with evidence:**

| Guardrail | Where |
|---|---|
| Key entered locally through Settings | `settings.save_key`, Settings screen |
| No key ships in the package | Key lives in `~/.rrf-app.env`; Section 8 excludes every env file |
| Only availability and last four reach Settings | `settings.status()` returns exactly `key_set` and `ends_with` |
| AI runs only after Mark asks | `POST /api/jobs/{name}/captions` fires from the "Suggest captions" button; nothing captions on open |
| Manual captions always available | Only blank captions are drafted; anything typed is left alone (`main.py:389,405`) |
| AI receives only selected photos | `photos_routes.included(manifest)` plus `_resolve_confined` per file (`main.py:386-394`) |
| AI receives only approved job context | `manifest.get("context")`, the job's own recorded context, and nothing else |
| No general filesystem access | Every path is resolved and confined to the job's `Photos` folder before opening |
| Cannot move, rename, edit, or delete sources | The AI path opens images read-only and writes only the app-owned manifest |
| Never log the key | Key is handed to the client explicitly and never printed; no logging calls in the server path |

**Missing, and built in this plan:**

| Gap | What is true today | What the pilot needs |
|---|---|---|
| Photo count before sending | The button says "Suggest captions" and prose mentions "a dozen"; no real number | The screen states the exact count of photos that will be sent, before he acts |
| Captions remain drafts until reviewed | `draft_job_captions` writes straight into the manifest with `save_manifest` (`main.py:403-407`) | See Section 14, question 3 |
| Request size bounded | Every blank photo goes in one request; a 60-photo job sends 60 images at once | A hard cap per request, batched, with a hard cap per run |
| Retries bounded | SDK default retries apply; nothing is set explicitly | An explicit `max_retries` on the client |
| Spending bounded | Nothing | A per-run photo ceiling and an explicit refusal above it |
| Never log client content | No logging in the server path, but the two CLI tools print job names and filenames | Assert it, and keep the CLI tools out of the package (Section 8) |

## 4. Embedded Python and dependencies

**Distribution.** The Windows embeddable package (`python-3.12.x-embed-amd64.zip`).
Chosen over 3.9 because 3.9 is past end of life and Windows wheel coverage for
the pinned set is materially better on 3.12. The source stays 3.9 compatible
per the roadmap, so this is a runtime choice, not a language choice.

**Assembly, all from the Mac:**

1. Download the embeddable zip and expand it into `build/windows/python/`.
2. Edit `python312._pth` to uncomment `import site`, so a `site-packages`
   directory is honoured. The embeddable distribution ignores it otherwise.
3. Fetch Windows wheels without installing them locally:
   `pip download -r app/server/requirements.txt --platform win_amd64 --python-version 3.12 --only-binary=:all: -d build/windows/wheels`
4. Install those wheels into the package:
   `pip install --no-index --find-links build/windows/wheels --target build/windows/python/site-packages -r app/server/requirements.txt`

**Known risks, named now.** `uvicorn[standard]` pulls `uvloop`, which is
POSIX-only and is skipped on Windows by its own environment marker;
`httptools` and `watchfiles` do publish Windows wheels. `pillow`,
`pillow-heif`, and `pydantic-core` are binary and must resolve as `win_amd64`
wheels or step 3 fails loudly. `pytest` and `httpx` are test-only and are not
installed into the package.

**What this proves and does not prove.** Step 3 failing on the Mac proves a
wheel is unavailable. Step 3 succeeding does not prove the wheels import on
Windows. That is a Windows acceptance item.

## 5. How the built web interface enters the package

`app/web/dist` is produced on the Mac by `cd app/web && npm ci && npm run build`
and copied into the package as `app/web/dist`. Nothing else from `app/web`
ships: no `src`, no `node_modules`, no `package.json`. Mark never has Node,
and the packaging step fails loudly if `dist` is missing or older than `src`,
rather than shipping a stale interface.

`main.py:522` already resolves `dist` relative to the server file, so the
mount works unchanged inside the package.

## 6. The Windows launcher

**Design decision: the logic lives in Python, the `.bat` is a thin shim.**
HOW-WE-WORK says nothing but Python runs on Mark's machine, and a port check
written twice (once in bash, once in batch) is a defect waiting to happen.
So `run_app.py` grows the startup logic and both platforms share it.

`Start Roy R. Fisher.bat` does exactly three things: change to its own folder,
run `python\python.exe app\run_app.py`, and `pause` on failure so the window
stays open with the reason visible.

`run_app.py` gains, in order:

1. **Is it already running?** Probe `http://127.0.0.1:8000/api/demo`. A JSON
   answer means our app is up: open the browser at it and exit 0 without
   starting a second copy. This is what the `.command` does today with `curl`,
   moved into Python.
2. **Is the port occupied by something else?** If the probe connects but does
   not answer as our app, walk up from 8000 to the first free port and use it.
   The browser is opened at the port actually bound, never at 8000 by
   assumption.
3. **Start, then wait for a real answer.** Today the browser opens on a
   one-second timer, which is a guess. Instead poll the bound port until it
   answers, up to a bounded timeout, then open the browser. This is the whole
   of "never open a dead browser page".
4. **Report failure in plain words.** If the server never answers within the
   timeout, print what was tried, the port, and what to do next, and exit
   non-zero so the `.bat`'s `pause` holds the window open. No traceback as the
   only output.

The Mac `.command` is reduced to the same thin shim so both platforms take the
same path.

## 7. Settings and keys across versioned pilot updates

Nothing to migrate, and that is the point. All three app-owned files already
live in Mark's home folder:

| File | Holds |
|---|---|
| `~/.rrf-app.env` | The API key |
| `~/.rrf-app.json` | The chosen jobs folder and the active job list |
| `~/.rrf-classifications.json` | What Mark said each file is |

Unzipping `Roy R. Fisher v0.2.0` beside `v0.1.0` therefore carries his key,
his folder choice, and his classifications with no action from him and no
update code. A new test asserts the package writes nothing inside itself at
run time, so this stays true.

## 8. Exact package contents and exclusions

**Layout.** One versioned top folder so nothing overwrites a prior pilot:

```
Roy R. Fisher v0.1.0/
  Start Roy R. Fisher.bat
  README FIRST.txt          plain instructions for Mark
  VERSION                   the version string, read and shown in the app
  python/                   embedded runtime + site-packages
  app/
    run_app.py
    data/  engine/  server/  templates/
    web/dist/
```

**Included:** `run_app.py`, `app/data`, `app/engine`, `app/server`,
`app/templates`, `app/web/dist`, the embedded runtime, the launcher, the
readme, the version file.

**Excluded, every one asserted by a packaging test:**

- `app/tests` and every test artifact
- `app/web/src`, `app/web/node_modules`, `package.json`, `package-lock.json`
- `app/server/demo.py` and the demo reset route (development-only control)
- `RRF Demo Jobs/` and any demo or client material
- `brand/`, `docs/`, `.git/`, `Report Examples/`
- `__pycache__/`, `.pytest_cache/`, `.DS_Store`
- any `.env` file, any key, any cache, any thumbnail cache
- `Start Roy R. Fisher.command` (the Mac launcher)
- the two CLI entry points' dev use, by virtue of nothing invoking them

Excluding `demo.py` means `main.py` must import it conditionally and register
neither demo route when it is absent. Today `demo.enabled()` already gates the
reset, so this is defence in depth: the control is gated *and* not present.

## 9. Mac regression tests

Everything below runs on the Mac and must be green before any package is sent.

| Test file | Proves |
|---|---|
| existing suite | Nothing regressed. Baseline at branch point: 320 passed, 15 skipped |
| `test_output_naming.py` | The base name is built from confirmed values only; Windows-forbidden characters are stripped; an existing file produces a numbered copy; a missing confirmed value refuses rather than guesses |
| `test_caption_guards.py` | Batch size is capped; the per-run ceiling refuses above it; `max_retries` is set explicitly; the count endpoint reports the true number of photos that would be sent |
| `test_package_manifest.py` | The packaging list includes every required path and excludes every path in Section 8, asserted against a built package tree |
| `test_launcher.py` | Port selection picks a free port, detects our own running app, and never reports success without a real answer |
| `test_file_safety.py` (existing) | Still green. Never weakened |

## 10. Windows acceptance steps on Mark's actual computer

The thirteen steps, in order, exactly as authorized. The pilot is not proven
until every one passes on his machine:

1. Receive the versioned package.
2. Unzip once.
3. Double-click once.
4. Browser opens to the working app.
5. Select the real parent jobs folder.
6. Configure the API key through Settings.
7. Open one job.
8. Draft captions with the guarded AI flow.
9. Review or edit captions.
10. Build `City_Address Photos (Complete).docx`.
11. Open the Word document.
12. Confirm all source files remain unchanged.
13. Stop and restart the app successfully.

Step 12 is checked the way Phase 0 checked it: sizes and modification times of
every file in the job before and after, compared, with the built output the
only new file.

## 11. Provable on the Mac, versus requires Windows

**Provable on the Mac:** every guardrail's logic, the filename rules, the
non-overwrite behavior, the port selection and failure reporting, the package
contents and exclusions, the wheel *availability* for `win_amd64`, and the
whole existing suite.

**Requires Windows, and is honestly unproven until then:** that the embedded
runtime starts at all, that the binary wheels import, that the `.bat`
double-click works from an unzipped folder, that the browser opens, that Word
opens the output, that `Path.home()` resolves to his profile as expected, and
that a second unzipped version runs without disturbing the first.

No claim in any report will say the pilot works on Windows before it has run
on Windows.

## 12. Rollback

The package is versioned and self-contained, and every piece of Mark's state
lives outside it. So rollback is: keep the previous version's folder, and
double-click its launcher instead. Nothing is uninstalled, nothing is
migrated, and no state is lost either direction.

The instruction to Mark is one line in `README FIRST.txt`: keep the previous
folder until the new one has worked once.

There is no automatic updater in this slice, by decision.

## 13. Exact stop conditions

Stop and report, without proceeding, when any of these is true:

1. `test_file_safety.py` fails, or any test shows a source file changed.
2. A wheel has no `win_amd64` build, so the package cannot be assembled.
3. The suite is not green at the end of any task.
4. A packaging step would include anything in the Section 8 exclusion list.
5. The confirmed city or address is unavailable and the code would have to
   infer either one.
6. Any Windows acceptance step fails on Mark's machine.
7. Any choice appears that materially affects Mark's setup, AI spending,
   privacy, file safety, or update experience and is not already settled here.
8. The work would touch Description of Improvements. It does not begin in this
   session.

## 14. Open questions for Spenser, before implementation

Three choices in this plan are Spenser's, not the executor's. Implementation
of the affected parts does not start until they are answered. Everything else
in the plan is unblocked.

**Question 1: where do the confirmed city and address come from?**
This is the blocking one. The app does not store them today. `create_job`
takes city and street, uses them to propose a folder name, and discards both
(`jobs.py:55-61,114-131`). `job-brief.md` holds a single free-text "Property
address" with no separate city. The folder name encodes `CITY_Address`, but
reading them back out of it is inference from a name, which the locked
behavior forbids and which HOW-WE-WORK forbids separately.

**Question 2: what is the ceiling on one captioning run?**
This sets Mark's worst-case spend per click. It needs a number for photos per
request, a number for photos per run, and a retry count.

**Question 3: do drafted captions save immediately, or wait for review?**
Today they are written into the manifest as soon as they come back, then
edited on screen. The locked behavior says captions remain drafts until Mark
reviews them, which reads as a real change.

Recommendations for all three are in the chat message accompanying this plan.

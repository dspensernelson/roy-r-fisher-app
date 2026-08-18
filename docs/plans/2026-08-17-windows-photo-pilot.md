# Windows Photo Pilot implementation plan

Written 2026-08-17 on branch `windows-photo-pilot`, cut from `main` at the
Phase 0 merge (`5b7ee7c`). Authorized by the roadmap decision of 2026-08-17,
"Mark receives an early Windows Photo Pilot, before the handoff bundle".
Reconciled 2026-08-18 with the product decisions Spenser approved that day.

**Goal.** Mark receives a versioned Windows package that he unzips once,
launches with one double-click, points at his jobs folder, sets up guarded AI
captions, and uses to build Subject Photograph pages. No Python, no Node, no
Terminal, no development tools.

**What this is not.** Not the Phase 1 Windows Office proof: photo pages need
no Office at all, so nothing here says anything about Excel, Word automation,
or PDF through COM. Not the complete handoff through Phase 3. Not Phase 5
final packaging. No Description of Improvements work of any kind.

**Status of this document.** A plan, not implementation authorization. The
product decisions in it are approved. The technical design is not settled:
every packaging, launcher, and updater proposal below is pending independent
technical review, and none of it has run on Windows.

## How to read the labels

This plan mixes things that are known with things that are not, so every claim
carries one of four labels. Nothing unlabeled is load bearing.

- **FACT.** Verified in the code or on disk on the stated date, with a
  pointer.
- **APPROVED.** A product decision Spenser has explicitly made.
- **PROPOSAL.** A recommendation, not settled, and not authorization to build.
- **OPEN.** An unresolved question. Whose it is, is stated with it.

## Global constraints

- `HOW-WE-WORK.md` governs. Its Never list has no judgement in it, and its
  Approval section governs what reaches Spenser and when.
- Python 3.9 compatible source: no `int | None` unions, no `match`. Verified
  clean across `app/server`, `app/engine`, and `app/run_app.py` on 2026-08-17.
- No em dashes anywhere: code, comments, docs, UI copy, launcher text.
- Never write into `Report Examples/` or `locker/`. Neither exists inside this
  repository, and neither is ever copied in.
- Never commit, log, display, or place the key in a job folder. Tests use fake
  keys only.
- The suite must end green after every task: `python3 -m pytest app/tests -q`
- Commits on this branch are recovery checkpoints. Nothing is pushed, opened
  as a pull request, or merged without Spenser's yes.

---

## 1. What currently works unchanged

**FACT**, inspected 2026-08-17 and 2026-08-18 at `5b7ee7c`. None of this needs
changing for the pilot.

| Area | State | Evidence |
|---|---|---|
| Server and web on one port | `run_app.py` starts uvicorn on 127.0.0.1:8000 and `main.py` mounts `app/web/dist` at `/` | `main.py:517-542` |
| Jobs folder selection | Chosen on a screen, remembered in `~/.rrf-app.json` | `workspace.py:23,35-39` |
| Key entry and display | Saved to `~/.rrf-app.env`, last four only ever reaches the browser | `settings.py:97-101` |
| Key file robustness | Reads `export`, indented, and quoted forms; save and remove match all of them | `settings.py:62-79,120-143` |
| Photo manifest and cuts | Reversible cuts, hand-editable manifest, 400 on malformed JSON | `photos.py`, Phase 0 Task 3 |
| Photo document build | Real Word file from the shipped template | `photo_pages.build_photo_docx` |
| Non-overwrite output | Counts up until a free name is found; never returns an existing filename | `photo_pages.next_output_name:54-69` |
| Windows-safe naming | `WINDOWS_FORBIDDEN` strip already used for folder names | `jobs.py:52,59` |
| Home-folder paths | `Path.home()` for key, settings, classifications | `settings.py:28`, `workspace.py:39`, `classify.py:46` |
| No Mac-only calls | No `subprocess`, `osascript`, or POSIX-only call anywhere in the app path | grep, 2026-08-17 |
| Demo reset already off | `demo.enabled()` gates the route; the button never renders unconfigured | `main.py:113-125` |

Two consequences worth stating. The non-overwrite machinery already exists, so
the filename work is a change of base name, not new safety. And every piece of
app-owned state already lives in the home folder, outside the package, so
versioned pilot updates preserve Mark's setup with no migration code.

## 2. Output naming

**FACT, corrected 2026-08-17.** An earlier version of this plan said the app
discards city and street. That was wrong. Intake requires both and refuses
without them (`main.py:219-226`), then writes them into `job-brief.md` itself,
joined in a known order, street then city then state (`main.py:240-243`). A job
the app made records "5675 Forest, Bettendorf, Iowa" in a field the app wrote.
The folder name carries the same two values a second time, as
`BETTENDORF_5675 Forest - 2026`.

**FACT.** `read_brief` is deliberately tolerant of briefs written by hand or by
the older onboarding skill (`brief.py:48-53`), so an older brief may not follow
that order and may carry no city.

**FACT.** Reading the engagement letter would be the natural source and is not
available. It is offered on the New Job screen but not built (`README.md`,
`NewJob.jsx:60`) and is Phase 4 work.

**APPROVED, 2026-08-18:**

- Read city and address from `job-brief.md`.
- Display both values near the Build action.
- Allow Mark to correct them before building.
- Store corrections in app-owned data outside the job folder.
- Do not infer them from the folder name.
- Output filename is `City_Address Photos (Complete).docx`.
- Sanitize Windows-invalid filename characters.
- Never overwrite an existing output. Create a numbered copy on collision.

**What changes in code:**

1. **A shared filename sanitizer.** `jobs.py:52-61` already strips
   `WINDOWS_FORBIDDEN`, collapses whitespace, trims trailing dots and spaces,
   and caps length. That logic moves to one helper both the folder namer and
   the output namer call, so the two cannot drift.
2. **`next_output_name` takes the base name.** Signature becomes
   `next_output_name(photos_dir, base)`. The counting loop is unchanged.
3. **A reader for the two values,** from the brief, with a correction stored
   app-side alongside classifications, outside Mark's folders.
4. **Build refuses** when neither the brief nor a correction yields a city and
   an address. It does not guess, and it does not fall back to the old
   `Photo (RRF App)` name.

**What is not changed.** The counting loop, the confinement checks, the
template, and the layout engine. No existing generated output is touched.

## 3. AI captioning: guardrails and the approved workflow

### 3a. Already in place

**FACT**, each with evidence:

| Guardrail | Where |
|---|---|
| Key entered locally through Settings | `settings.save_key`, Settings screen |
| No key ships in the package | Key lives in `~/.rrf-app.env`; Section 9 excludes every env file |
| Only availability and last four reach Settings | `settings.status()` returns exactly `key_set` and `ends_with` |
| AI runs only after Mark asks | `POST /api/jobs/{name}/captions` fires from a button; nothing captions on open |
| Manual captions always available | Only blank captions are drafted; anything typed is left alone (`main.py:389,405`) |
| AI receives only selected photos | `photos_routes.included(manifest)` plus `_resolve_confined` per file (`main.py:386-394`) |
| AI receives only approved job context | `manifest.get("context")` and nothing else |
| No general filesystem access | Every path is resolved and confined to the job's `Photos` folder before opening |
| Cannot move, rename, edit, or delete sources | The AI path opens images read-only and writes only the app-owned manifest |
| Never log the key | Handed to the client explicitly, never printed; no logging calls in the server path |

### 3b. Missing today

**FACT:**

| Gap | What is true today |
|---|---|
| Any cost or count shown before sending | The button says "Suggest captions"; prose mentions "a dozen". No real number, no cost |
| Any cost shown afterward | Nothing. Usage is not read from the response |
| A run ceiling | Every blank photo goes in one request; a 60-photo job sends 60 images with no cap |
| Retry control | SDK default retries apply implicitly; nothing is set |
| A review state | `draft_job_captions` writes straight into the manifest with `save_manifest` (`main.py:403-407`). Nothing marks a caption unreviewed, and Build does not care |

### 3c. The approved workflow

**APPROVED, 2026-08-18:**

**Sending.**

- Maximum 60 photos per AI-caption run.
- Show an estimated cost before sending, and the actual measured cost
  afterward when provider usage data permits.
- The estimate is **$0.05 per included photo**, calculated transparently and
  shown as the arithmetic, not just a total:

  | Included photos | Displayed estimate |
  |---|---|
  | 12 | 12 x $0.05 = $0.60 |
  | 60 | 60 x $0.05 = $3.00 |

- The figure is labeled on screen as an estimate.
- Use one API request when it fits. Split only when the provider's
  request-size constraints require it. Do not split into arbitrary batches of
  six.
- No automatic retries. A failed request shows a clear error and lets Mark
  retry deliberately.

**Reviewing.**

- AI captions save immediately as unreviewed drafts, so a refresh cannot lose
  paid work.
- Each included photo carries a small one-click `Reviewed` control beside or
  directly under its caption.
- The control is not called `Approve`.
- There is no `Approve all`.
- Visible progress, in the form `8 of 12 reviewed`.
- Editing a reviewed caption resets it to `Needs review`.
- Excluded photos do not require review.
- Build stays unavailable until every included caption has been reviewed.

**Note on the $0.05 figure, recorded so nobody mistakes it for a measurement.**
It is a deliberately conservative placeholder, and it is very likely higher
than the true per-photo cost. A 1024 pixel thumbnail runs roughly one to two
thousand input tokens, which at Opus-class input pricing lands nearer two cents
than five. Erring high is the safe direction for a number Mark reads before
spending money, so the figure stands as approved. It is still an estimate, it
is labeled as one, and the first real run records actual usage so it can be
corrected against evidence rather than arithmetic.

**OPEN, executor's question, not Spenser's.** The provider returns token usage
per response, not dollars. Turning usage into a dollar figure needs a price
table in the app, which goes stale when pricing changes. If a trustworthy
dollar figure cannot be derived, the screen shows measured token usage and says
plainly that the dollar figure is the estimate, not a measurement. That is what
"when provider usage data permits" means above. Resolved during implementation,
recorded in a code comment, no product decision required.

## 4. API key and spending controls

Two different things are involved and the plan keeps them apart, because only
one of them is code.

**Outside the app, controlled by Spenser at the provider. APPROVED,
2026-08-18:**

- A dedicated RRF Anthropic API key, controlled by Spenser.
- A **$20 spending limit**, set in the Anthropic console.
- Notifications go to Spenser.
- Mark does not manage billing.

**FACT.** None of the four items above is app behavior. They are provider
account settings. No code in this repository sets, reads, enforces, or verifies
any of them, and no test can assert them. The plan records them because they
are the hard financial guardrail, not because the app implements them.

**Inside the app, and therefore testable. APPROVED:**

- Mark enters the key through Settings.
- The key is never committed, logged, displayed, or placed in a job folder.
- The visible per-run estimate in Section 3c is the user-facing guardrail.
- The 60-photo ceiling is the hard in-app limit on a single run.

**What happens when the external limit is reached.** The app cannot see it
coming. The request fails, and Mark sees the clear error and the deliberate
retry from Section 3c, with no automatic retry burning further calls. That is
the intended behavior, not a gap.

## 5. Version and update direction

**APPROVED, 2026-08-18:**

- Display the installed app version on every screen.
- During the pilot, Spenser controls update installation.
- Mark does not independently install updates.
- No silent updates.
- Settings, API-key configuration, classifications, and the selected jobs
  folder must survive upgrades.
- **Record the last successfully started version in app-owned settings**, to
  support rollback.
- The eventual Windows installation should support self-contained versioned
  releases, last-known-good rollback, embedded runtime and dependencies,
  stable settings storage, port detection, and understandable startup
  failures.

**Stated plainly:** the list above is a set of approved requirements. It is not
proof that an updater architecture works, and it does not settle how any of it
is built. Every mechanism proposed in Section 16 is a proposal pending
independent technical review, and none of it has run on Windows.

**FACT, 2026-08-18.** No version string exists anywhere in the app today. Not
in `main.py`, not in `run_app.py`, not in `package.json`. Showing a version on
every screen is entirely new work: a `VERSION` file in the package, an endpoint
that reads it, and a place in the shared screen furniture that renders it.

**PROPOSAL for the last-good record, pending review.** Write it into the
existing `~/.rrf-app.json`, which is already the app-owned settings file, rather
than creating a fourth file in the home folder. Fewer files is fewer things to
migrate, and the approved wording says app-owned settings. The reviewer may
disagree; the record itself is approved, its location is not yet settled.

## 6. Embedded Python and dependencies

**PROPOSAL, pending independent technical review.** The Windows embeddable
package (`python-3.12.x-embed-amd64.zip`). Suggested over 3.9 because 3.9 is
past end of life and Windows wheel coverage for the pinned set is materially
better on 3.12. The source stays 3.9 compatible per the roadmap, so this would
be a runtime choice, not a language choice. Not settled.

**Assembly as currently imagined, all from the Mac:**

1. Download the embeddable zip and expand it into `build/windows/python/`.
2. Edit `python312._pth` to uncomment `import site`, so a `site-packages`
   directory is honoured. The embeddable distribution ignores it otherwise.
3. Fetch Windows wheels without installing them locally:
   `pip download -r app/server/requirements.txt --platform win_amd64 --python-version 3.12 --only-binary=:all: -d build/windows/wheels`
4. Install those wheels into the package:
   `pip install --no-index --find-links build/windows/wheels --target build/windows/python/site-packages -r app/server/requirements.txt`

**Risks, named now.** `uvicorn[standard]` pulls `uvloop`, which is POSIX-only
and is skipped on Windows by its own environment marker; `httptools` and
`watchfiles` do publish Windows wheels. `pillow`, `pillow-heif`, and
`pydantic-core` are binary and must resolve as `win_amd64` wheels or step 3
fails loudly. `pytest` and `httpx` are test-only and are not installed into the
package.

**What this would prove and would not prove.** Step 3 failing on the Mac proves
a wheel is unavailable. Step 3 succeeding does not prove the wheels import on
Windows. That is a Windows acceptance item.

No dependency is installed and no download is performed during this planning
checkpoint.

## 7. How the built web interface enters the package

**PROPOSAL, pending review.** `app/web/dist` is produced on the Mac by
`cd app/web && npm ci && npm run build` and copied into the package as
`app/web/dist`. Nothing else from `app/web` ships: no `src`, no `node_modules`,
no `package.json`. Mark never has Node, and the packaging step fails loudly if
`dist` is missing or older than `src`, rather than shipping a stale interface.

**FACT.** `main.py:522` already resolves `dist` relative to the server file, so
the mount works unchanged inside a package laid out this way.

## 8. The Windows launcher

**PROPOSAL, pending independent technical review. Not settled.** The logic
lives in Python and the `.bat` is a thin shim. HOW-WE-WORK says nothing but
Python runs on Mark's machine, and a port check written twice (once in bash,
once in batch) is a defect waiting to happen, so `run_app.py` would grow the
startup logic and both platforms would share it.

`Start Roy R. Fisher.bat` would do three things: change to its own folder, run
`python\python.exe app\run_app.py`, and `pause` on failure so the window stays
open with the reason visible.

`run_app.py` would gain, in order:

1. **Is it already running?** Probe `http://127.0.0.1:8000/api/demo`. A JSON
   answer means our app is up: open the browser at it and exit 0 without
   starting a second copy. This is what the `.command` does today with `curl`,
   moved into Python.
2. **Is the port occupied by something else?** If the probe connects but does
   not answer as our app, walk up from 8000 to the first free port and use it.
   The browser is opened at the port actually bound, never at 8000 by
   assumption.
3. **Start, then wait for a real answer.** **FACT:** today the browser opens on
   a one-second timer (`run_app.py:12`), which is a guess. Instead poll the
   bound port until it answers, up to a bounded timeout, then open the browser.
   That is the whole of "never open a dead browser page".
4. **Report failure in plain words.** If the server never answers within the
   timeout, print what was tried, the port, and what to do next, then exit
   non-zero so the `.bat`'s `pause` holds the window open. No traceback as the
   only output.

The Mac `.command` would be reduced to the same thin shim so both platforms
take the same path.

## 9. Package contents and exclusions

**PROPOSAL for the layout, pending review.** One versioned top folder so
nothing overwrites a prior pilot:

```
Roy R. Fisher v0.1.0/
  Start Roy R. Fisher.bat
  README FIRST.txt          plain instructions for Mark
  VERSION                   the version string, read and shown on every screen
  python/                   embedded runtime + site-packages
  app/
    run_app.py
    data/  engine/  server/  templates/
    web/dist/
```

**Included:** `run_app.py`, `app/data`, `app/engine`, `app/server`,
`app/templates`, `app/web/dist`, the embedded runtime, the launcher, the
readme, the version file.

**Excluded. The exclusion list itself is not a proposal: it is a requirement,
and every line is asserted by a packaging test.**

- `app/tests` and every test artifact
- `app/web/src`, `app/web/node_modules`, `package.json`, `package-lock.json`
- `app/server/demo.py` and the demo reset route (development-only control)
- `RRF Demo Jobs/` and any demo or client material
- `brand/`, `docs/`, `.git/`, and anything from `Report Examples/` or `locker/`
- `__pycache__/`, `.pytest_cache/`, `.DS_Store`
- any `.env` file, any key, any cache, any thumbnail cache
- `Start Roy R. Fisher.command` (the Mac launcher)

Excluding `demo.py` means `main.py` must import it conditionally and register
neither demo route when it is absent. **FACT:** `demo.enabled()` already gates
the reset (`main.py:120-125`), so this is defence in depth: the control is
gated and also not present.

## 10. Representing unfinished features honestly

**APPROVED, 2026-08-18:**

- Unfinished capabilities sit in a visually separate section titled
  `Planned workflows`.
- **That section shows exactly one item: `Description of Improvements`,**
  marked `Not available in this pilot`.
- The item is disabled.
- Do not use `Coming soon`.
- Do not show release dates or imply a delivery promise.
- Do not create controls that appear clickable but do nothing.
- The working Subject Photos workflow must be visually distinct from this
  informational content.
- Identify the smallest appropriate screen placement, and do not implement it
  in this checkpoint.

**To be unmistakable:** naming `Description of Improvements` on a disabled row
is the whole of the Description of Improvements work in this pilot. No
template is read, no structure is decided, no implementation plan exists, and
none is approved. The roadmap decision of 2026-08-17 stands: nothing begins
until Mark's newer template is received and inspected.

**FACT, current behavior.** The section picker already lists every section the
report needs and says plainly that only photos build (`README.md`). So the
honest-representation problem is partly solved already, and the pilot's job is
to make the boundary unmistakable rather than to invent a new listing.

**PROPOSAL: smallest placement, pending review.** One band at the bottom of the
job screen (`JobHome.jsx`), below the folder bands, titled `Planned workflows`,
holding one plain non-interactive row. Reasons: the job screen is the one
screen Mark returns to, the folder bands above it already establish the band
pattern, and a row there cannot be confused with an action because the actions
on that screen sit at the top on the title's row, per HOW-WE-WORK. No new route
and no new screen. Not implemented in this checkpoint.

## 11. The testing ground

**APPROVED, 2026-08-18.** A repeatable acceptance environment, in this order:

1. Begin with a disposable synthetic job containing safe test photos.
2. Test a normal 12-photo run.
3. Test the 60-photo maximum.
4. Confirm 61 photos are blocked before any API request or any cost occurs.
5. Never test against original evidence or client folders.
6. A copied real demo job may be used only after Spenser selects the copy and
   explicitly authorizes those photos for an external AI request.
7. Generated documents must use fresh output names and must not overwrite
   existing documents.

**How the block at 61 is proven without spending anything.** The ceiling is
checked before the client is constructed, so the refusal path never reaches the
network. The test asserts the refusal and asserts that no request was
attempted, using a stand-in for the model per HOW-WE-WORK's list of three
external conditions that may be stood in for. Cost of that test: zero.

**Synthetic photos.** Generated with Pillow, the way
`test_shipped_template.py` already does. They prove the mechanics of counting,
batching, refusing, reviewing, and naming. **They prove nothing about caption
quality**, which needs real photographs and is why item 6 exists.

## 12. Acceptance checklist

**APPROVED, 2026-08-18.** Seventeen items. The pilot is not proven until every
one passes.

1. Clean installation and first launch.
2. Jobs-folder selection.
3. API-key setup, and behavior with no key present.
4. Estimated cost shown before the request.
5. Actual cost or usage shown afterward.
6. Caption generation, and drafts persisting immediately.
7. Refresh and restart without losing paid caption work.
8. One-click review of every included caption.
9. Editing a reviewed caption resets its status.
10. Excluded photos do not block Build.
11. Build stays blocked while included captions remain unreviewed.
12. Exact output filename, and collision behavior.
13. Clear failure with no automatic retry.
14. Visible version number.
15. Upgrade from one test version to another without losing settings.
16. Rollback to the last working version.
17. Automated tests, a real screen walkthrough, and a real Windows-machine
    acceptance test remain separate evidence. One never stands in for another.

**No paid API test and no Windows installation test is performed during this
planning checkpoint.**

## 13. Mac regression tests

Everything below runs on the Mac and must be green before any package is sent.

| Test file | Proves |
|---|---|
| existing suite | Nothing regressed. Baseline at branch point: 320 passed, 15 skipped |
| `test_output_naming.py` | The base name comes from the brief or a stored correction, never the folder name; Windows-forbidden characters are stripped; an existing file produces a numbered copy; a missing value refuses rather than guesses |
| `test_caption_guards.py` | 60 is the ceiling; 61 refuses before any request is attempted; retries are off; the count and the $0.05 arithmetic shown before sending match what would be sent |
| `test_caption_review.py` | Drafts save immediately as unreviewed; a review marks one caption; editing a reviewed caption resets it; excluded photos never block; Build refuses while an included caption is unreviewed |
| `test_package_manifest.py` | The packaging list includes every required path and excludes every path in Section 9, asserted against a built package tree |
| `test_launcher.py` | Port selection picks a free port, detects our own running app, and never reports success without a real answer |
| `test_settings_survive_upgrade.py` | The three home-folder filenames are exactly as named, and the last-good version record round-trips |
| `test_file_safety.py` (existing) | Still green. Never weakened |

## 14. Provable on the Mac, versus requires Windows

**Provable on the Mac:** every guardrail's logic, the ceiling and the refusal
at 61, the cost arithmetic, the review state machine, the filename rules, the
non-overwrite behavior, the port selection and failure reporting, the package
contents and exclusions, the wheel availability for `win_amd64`, and the whole
existing suite.

**Requires Windows, and is honestly unproven until then:** that the embedded
runtime starts at all, that the binary wheels import, that the `.bat`
double-click works from an unzipped folder, that the browser opens, that Word
opens the output, that `Path.home()` resolves to his profile as expected, and
that a second unzipped version runs without disturbing the first.

**Requires a real paid run:** whether the $0.05 estimate is close, and caption
quality on real photographs.

No report will say the pilot works on Windows before it has run on Windows.

## 15. Rollback

**PROPOSAL, pending review.** The package is versioned and self-contained, and
every piece of Mark's state lives outside it. So rollback would be: keep the
previous version's folder, and double-click its launcher instead. Nothing is
uninstalled, nothing is migrated, and no state is lost in either direction. The
last-good version record from Section 5 exists so a report can say which
version actually last started.

The instruction to Mark would be one line in `README FIRST.txt`: keep the
previous folder until the new one has worked once.

There is no automatic updater in this slice, by decision. During the pilot
Spenser installs updates; Mark does not.

## 16. Updater and packaging: technical review

**Everything in this section is a proposal pending independent technical
review. None of it is settled, and none of it has run on Windows.** The
reviewer may identify risks and alternatives. The reviewer may not make product
decisions.

### 16a. Current startup and installation behavior

**FACT, 2026-08-18:**

- There is no installation. The app runs from a git clone.
- `Start Roy R. Fisher.command` is bash: it `cd`s to its own folder, probes
  `http://127.0.0.1:8000` with `curl`, opens the browser with `open` if the app
  answers, otherwise runs `python3 app/run_app.py`.
- `run_app.py` is 13 lines. It hardcodes port 8000, opens the browser on a
  1.0 second `threading.Timer`, and calls `uvicorn.run`.
- There is no port-conflict handling, no readiness check, no failure message,
  and no exit code discipline.
- There is no packaging tooling of any kind in the repository.
- There is no version string anywhere.

### 16b. Where settings and secrets currently live

**FACT:**

| Path | Holds | Written by |
|---|---|---|
| `~/.rrf-app.env` | The Anthropic API key, mode 0600 where the OS supports it | `settings.py:38-47` |
| `~/.rrf-app.json` | The chosen jobs folder and the active job list | `workspace.py:23,35-39` |
| `~/.rrf-classifications.json` | What Mark said each file is | `classify.py:46` |

All three resolve through `Path.home()`, which is correct on Windows, and all
three are overridable by environment variable for tests. None sits inside the
repository or inside a job folder.

### 16c. What must remain stable between versions

The three paths in 16b, their filenames, and their on-disk shapes, plus the
approved last-good version record. A version that renames or reshapes any of
them silently loses Mark's setup, which is acceptance item 15.

**PROPOSAL.** Treat those filenames as a compatibility surface: a test asserts
the literal names, so a rename becomes a deliberate act with a migration
attached rather than an accident.

### 16d. Version-folder and last-known-good concepts

**APPROVED product requirement:** the last successfully started version is
recorded in app-owned settings.

**PROPOSAL for how, not settled:**

- Each release unzips to its own `Roy R. Fisher vX.Y.Z/` folder. Nothing
  overwrites a prior version, which would be the whole rollback mechanism.
- The record lives in the existing `~/.rrf-app.json` rather than a fourth
  home-folder file, per Section 5.
- "Last known good" is whichever version folder last started successfully.
  Since state is external, that is a folder to re-launch, not a state to
  restore.
- **OPEN, for the reviewer.** What counts as "started successfully". Bound to
  the port, or answered one request, or rendered one screen. The three differ,
  and the weakest of them would record a version that starts and then fails.

### 16e. Update download, integrity, and rollback questions

**OPEN, all of them, and all deliberately unanswered here:**

- How the package reaches Mark. Email attachment, a link, a shared folder. Each
  has a different failure mode and a different size limit, and a package with
  an embedded runtime is not small.
- Whether integrity is verified at all, and how. A checksum Mark is asked to
  compare is a second step on his machine, which HOW-WE-WORK calls a defect.
  A checksum nobody checks is decoration.
- Whether an interrupted unzip can be detected. A partial extraction that still
  contains a launcher is the dangerous case: it starts, and then fails
  somewhere less obvious.
- **PROPOSAL toward that last one, pending review:** the launcher verifies a
  small manifest of expected files before starting, and refuses with a plain
  message naming what is missing. Cheap, local, no network, and it would turn a
  confusing runtime failure into an understandable startup failure.

### 16f. Windows risks

**Risks, not yet mitigated and not yet measured:**

- **Antivirus and SmartScreen.** An unsigned `.bat` that launches a bundled
  `python.exe` and opens a listening socket is a recognisable pattern to
  endpoint protection. It may be blocked, quarantined, or delayed.
  **APPROVED, 2026-08-18:** do not purchase or require code signing for Mark's
  pilot. Reconsider it before wider distribution. So this risk is accepted for
  the pilot, and mitigation, if any is needed, is procedural: Spenser is present
  by screen share when Mark first launches it.
- **Permissions.** Unzipping into `Program Files` needs elevation and would
  break the write-nothing-inside-the-package assumption. Mark should unzip into
  his own profile, for example the Desktop or Documents. That belongs in
  `README FIRST.txt`.
- **Port conflict.** Section 8's walk-up would handle a busy 8000. Not handled:
  a corporate proxy or a security product that intercepts localhost traffic.
- **Path length.** A deep unzip location plus `site-packages` plus long wheel
  paths can approach the legacy 260 character limit on machines where long
  paths are not enabled. Mitigated by unzipping near the top of the profile,
  and worth an explicit check in the manifest verification above.
- **Blocked outbound HTTPS.** Captions need `api.anthropic.com`. If it is
  blocked, the app must degrade to typed captions and say so, which it already
  does when no key is present. **OPEN:** whether a blocked network produces the
  same clear message as a missing key, or a worse one.

### 16g. The smallest technical spike that would prove the design

**PROPOSAL, pending review.** One spike, on Windows, before any pilot feature
work:

Assemble a package containing the embedded runtime, the installed wheels, the
built interface, and today's unmodified app. Unzip it on Windows. Double-click.
Confirm the browser opens the working app, that the three home-folder files
appear in Mark's profile, and that stopping and restarting works. Then unzip a
second copy beside it and confirm both run and share the same settings.

**What that spike would settle:** the embedded runtime, the binary wheels, the
launcher, the browser open, `Path.home()`, and the versioned-folder rollback
premise. Six of the largest unknowns, with no pilot feature code written and no
paid API call.

**What it would not settle:** captions, cost, filenames, review state, or
anything about Office.

### 16h. Alternatives and tradeoffs where the answer is not proven

| Question | Options | Tradeoff |
|---|---|---|
| Runtime | Embeddable zip; full installer; PyInstaller or Nuitka single file | Embeddable is transparent and debuggable but needs the `._pth` edit and a manual wheel step. A frozen binary is one file and a nicer double-click, but it is opaque when it fails and is much more likely to alarm antivirus |
| Launcher | `.bat`; `.vbs` to hide the console; a signed `.exe` shim | The `.bat` shows a console window, which is ugly but is also the only place a plain failure message can land. Hiding it makes failure invisible. The signed shim is out, per the approved no-signing decision |
| Runtime version | 3.12 embeddable; 3.9 to match the proven pins | 3.12 has better wheel coverage but the pinned set was proven on 3.9. Either way the Windows install is a fresh proof |
| Update delivery | Full package each time; a diff or patch | Full is simple and matches versioned folders and rollback. Patching is smaller but introduces exactly the interrupted-update failure mode 16e worries about |
| Version display | A `VERSION` file read at startup; a constant in the source | A file is what packaging writes and rollback distinguishes. A constant cannot drift from the code but cannot be inspected without running the app |
| Last-good record | Inside `~/.rrf-app.json`; a separate fourth file | One file is less to migrate and matches the approved "app-owned settings" wording. A separate file cannot be corrupted by an unrelated settings write |

**Not chosen on convenience.** The embeddable runtime and the full-package
update are recommended because they keep failure legible and rollback trivial,
not because they are the least work. The frozen single-file binary is less work
to hand over and is recommended against for the pilot precisely because a pilot
exists to produce diagnosable failures. The reviewer is invited to disagree
with any of it.

## 17. Exact stop conditions

Stop and report, without proceeding, when any of these is true:

1. `test_file_safety.py` fails, or any test shows a source file changed.
2. A wheel has no `win_amd64` build, so the package cannot be assembled.
3. The suite is not green at the end of any task.
4. A packaging step would include anything in the Section 9 exclusion list.
5. The confirmed city or address is unavailable and the code would have to
   infer either one.
6. A run would send more than 60 photos, or would send anything before the
   count and the cost estimate have been shown.
7. Any acceptance item in Section 12 fails.
8. Any choice appears that materially affects Mark's setup, AI spending,
   privacy, file safety, delivery, permissions, or scope and is not already
   approved here.
9. The work would touch Description of Improvements beyond the single disabled
   row named in Section 10.

## 18. Decisions still needed

**From Spenser: none.** Every product question this plan raised on 2026-08-17
was answered on 2026-08-18. The estimate is $0.05 per included photo shown as
arithmetic, the provider limit is $20 with notifications to Spenser, the
`Planned workflows` section shows Description of Improvements alone, the
last-good version is recorded in app-owned settings, and code signing is out
for the pilot and revisited before wider distribution.

**From the independent technical reviewer**, before implementation:

1. Whether the embeddable runtime and manual wheel step is the right shape at
   all, against a frozen binary or a full installer (16h).
2. What counts as "started successfully" for the last-good record (16d).
3. How the package reaches Mark, and whether integrity is verified (16e).
4. Whether a partial extraction can be detected, and whether the manifest check
   is the right mitigation (16e).
5. Whether the port walk-up is sufficient, or whether localhost interception
   needs handling (16f).

**Not authorization.** Approval of this plan's product decisions is not
approval to implement. Implementation waits on Spenser's review of this
reconciled plan and on the independent updater review.

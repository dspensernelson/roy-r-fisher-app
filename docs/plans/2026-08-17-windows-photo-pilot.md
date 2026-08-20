# Windows Photo Pilot implementation plan

Written 2026-08-17 on branch `windows-photo-pilot`, cut from `main` at the
Phase 0 merge (`5b7ee7c`). Authorized by the roadmap decision of 2026-08-17,
"Mark receives an early Windows Photo Pilot, before the handoff bundle".
Reconciled 2026-08-18 with the product decisions Spenser approved that day.
Reconciled again 2026-08-18, after an independent technical review of the
packaging, launcher, updater, and state design, with the six recommendations
Spenser approved from it and the report photo optimization he approved
alongside them. Corrected 2026-08-19 with the adaptive cost estimate and local
run history, the package-integrity repair, and the execution plan.

**Goal.** Mark receives a versioned Windows package that he unzips once,
launches with one double-click, points at his jobs folder, sets up guarded AI
captions, and uses to build Subject Photograph pages. No Python, no Node, no
Terminal, no development tools.

**What this is not.** Not the Phase 1 Windows Office proof: photo pages need
no Office at all, so nothing here says anything about Excel, Word automation,
or PDF through COM. Not the complete handoff through Phase 3. Not Phase 5
final packaging. No Description of Improvements work of any kind.

**Status of this document.** A plan, not implementation authorization. The
product decisions in it are approved. The technical direction in it is approved
too. As of 2026-08-19 it also carries an execution plan, Section 26, with eight
bounded tasks and four approval gates. Approval of a technical direction is not
proof that it works and is not a record that it was built. Task 1 is complete
and its evidence is in Section 7a. Nothing in this document has run on Windows,
and no task after Task 1 has started.

## How to read the labels

This plan mixes things that are known with things that are not, so every claim
carries one of five labels. Nothing unlabeled is load bearing.

- **FACT.** Verified in the code or on disk on the stated date, with a
  pointer.
- **APPROVED.** A product decision Spenser has explicitly made.
- **DIRECTION.** A technical approach Spenser has approved. Approved is not
  proven and is not built. Every DIRECTION item still needs its tests to
  pass before anything about it may be reported as working.
- **UNPROVEN.** A Windows assumption nobody has tested. It becomes FACT only
  after it has run on Windows.
- **TEST.** Required before acceptance. Listed so no item can be quietly
  dropped.
- **OPEN.** Still unresolved. Whose question it is, is stated with it.

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
- Never modify, replace, rename, move, or recompress one of Mark's original
  photographs. See Section 12.
- The suite must end green after every task: `python3 -m pytest app/tests -q`
- Commits on this branch are recovery checkpoints. Nothing is pushed, opened
  as a pull request, or merged without Spenser's yes.

---

## 1. What currently works

**FACT**, inspected 2026-08-17 and re-verified 2026-08-18 at `c5d5da1`. This is
the state of the code as it stands. Most of it needs no change for the pilot.
Two rows do change and say so, so this table cannot be read as a promise that
nothing in it moves.

| Area | State | Evidence |
|---|---|---|
| Server and web on one port | `run_app.py` starts uvicorn on 127.0.0.1:8000 and `main.py` mounts `app/web/dist` at `/`. **This one changes:** the host stays 127.0.0.1, the fixed port 8000 does not survive Section 5b | `run_app.py:13`, `main.py:517-542` |
| Jobs folder selection | Chosen on a screen, remembered in `~/.rrf-app.json` | `workspace.py:23,35-39` |
| Key entry and display | Saved to `~/.rrf-app.env`, last four only ever reaches the browser | `settings.py:97-101` |
| Key file robustness | Reads `export`, indented, and quoted forms; save and remove match all of them | `settings.py:62-79,120-143` |
| Photo manifest and cuts | Reversible cuts, hand-editable manifest, 400 on malformed JSON | `photos.py`, Phase 0 Task 3 |
| Photo document build | Real Word file from the shipped template | `photo_pages.build_photo_docx` |
| Non-overwrite output | Counts up until a free name is found; never returns an existing filename. **This one changes:** the base name becomes an argument per Section 2. The counting loop and the safety do not change | `photo_pages.next_output_name:54-69` |
| Windows-safe naming | `WINDOWS_FORBIDDEN` strip already used for folder names | `jobs.py:52,59` |
| Home-folder paths | `Path.home()` for key, settings, classifications | `settings.py:28`, `workspace.py:39`, `classify.py:46` |
| No Mac-only calls | No `subprocess`, `osascript`, `os.system`, `pwd`, `fcntl`, `tkinter`, or `ctypes` anywhere in the app path. The one POSIX-only call, `chmod(0o600)`, is already wrapped and commented for Windows | grep 2026-08-18; `settings.py:42-47` |
| Demo reset already off | `demo.enabled()` gates the route; the button never renders unconfigured | `main.py:113-125` |
| Front end tolerates a missing demo route | `getDemo().then(setDemo).catch(() => {})`, so removing the route breaks no screen | `App.jsx:27` |

Two consequences worth stating. The non-overwrite machinery already exists, so
the filename work is a change of base name, not new safety. And every piece of
app-owned state already lives in the home folder, outside the package, so
versioned pilot updates preserve Mark's setup with no migration code.

### 1a. What the independent review found that this plan had not recorded

**FACT, 2026-08-18.** Four verified findings. Each one is acted on in a
section below, named here so none of them can be lost.

| Finding | Evidence | Acted on in |
|---|---|---|
| Only one of the three home-folder files is written safely. `classify.py` writes through a temporary file and `os.replace`. `workspace.py` and `settings.py` call `write_text` directly | `classify.py:63-79` versus `workspace.py:56-62` and `settings.py:38-47` | Section 6 |
| An unreadable settings file is treated as no settings at all, silently, with no message to Mark | `workspace.py:48-52`, and the same shape at `classify.py:55-59` | Section 6 |
| `busy.py` is a `threading.Lock`. It guards writes inside one process. Nothing guards two app processes writing the same home-folder files | `busy.py:31` | Section 5b |
| The document builder embeds the original image file. `add_picture(path, width=...)` stores the file's own bytes in the package and sets only the displayed width | `photo_pages.py:75` | Section 12 |

### 1b. A live defect found during the review

**FACT, 2026-08-18.** A `.heic` file placed directly into a job's `Photos`
folder makes Build fail today.

`PHOTO_EXTS` accepts `.heic` (`jobs.py:9`), so the app lists such a file,
thumbnails it, captions it, and includes it in the manifest. Build then hands
it to `add_picture` (`photo_pages.py:75`), and python-docx recognises only
PNG, JPEG, GIF, TIFF, and BMP by file signature. Verified against the pinned
`python-docx==1.2.0` on 2026-08-18 by reading its `SIGNATURES` table. A HEIC
raises `UnrecognizedImageError`.

The reason this has not bitten yet is that the upload route converts HEIC to
JPEG on the way in (`photos.py:230-235`), and testing has gone through upload.
Mark copies photos into his own folders directly, which is the path that fails.

This defect is fixed as a direct consequence of Section 12, because converting
the document copy to RGB JPEG makes a HEIC source embeddable. It is recorded
separately here so the fix is deliberate rather than incidental, and so the
HEIC test in Section 7 is understood as testing a known failure rather than
confirming a suspicion.

**APPROVED sequencing, 2026-08-19.** The defect is live on the Mac today, so
the question of when to fix it is real. The answer:

- The fix lands **inside Task 4's photo-optimization work**, per Section 26.
  Nothing separate is written for it.
- **Do not create a separate Mac hotfix** unless Spenser later asks for one.
- **HEIC dependency viability is still tested first, in Task 1**, because a
  missing `pillow-heif` wheel changes the Windows packaging path and that
  answer is needed before anything is packaged. Testing the dependency early
  and fixing the defect later are two different things, and both are
  deliberate.

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

**DIRECTION, 2026-08-18. This is parsing, not lookup.** The brief stores one
joined string, so recovering two values from it means splitting text. A street
carrying a comma, a unit number, a hand-written brief, or a brief from the
older onboarding skill can all split wrongly. The code must be written and
described as a parser that can be wrong, not as a field read.

Consequences that follow from that, and are required:

- A confident wrong split produces a wrong filename, which is cheap and
  visible. A missing value produces a refusal, which is also correct. Neither
  may produce a guess drawn from the folder name.
- Both parsed values are shown to Mark before Build, so a wrong split is
  visible before it reaches a filename.
- His correction is stored app-side and wins over the parse from then on.

**What changes in code:**

1. **A shared filename sanitizer.** `jobs.py:52-61` already strips
   `WINDOWS_FORBIDDEN`, collapses whitespace, trims trailing dots and spaces,
   and caps length. That logic moves to one helper both the folder namer and
   the output namer call, so the two cannot drift.
2. **`next_output_name` takes the base name.** Signature becomes
   `next_output_name(photos_dir, base)`. The counting loop is unchanged.
3. **A parser for the two values,** from the brief, with a correction stored
   app-side alongside classifications, outside Mark's folders.
4. **Build refuses** when neither the brief nor a correction yields a city and
   an address. It does not guess, and it does not fall back to the old
   `Photo (RRF App)` name.

**TEST, required before acceptance.** In `test_output_naming.py`:

- A street containing a comma parses without silently losing the city.
- A street containing a unit number parses without silently losing the city.
- A brief with no city refuses rather than guessing.
- A brief with neither value refuses rather than guessing.
- A brief in the older onboarding skill's order does not produce a confidently
  wrong pair without that being visible.
- A stored correction wins over the parsed value.
- A correction is stored outside the job folder and no job file is written.
- Windows-forbidden characters are stripped from the final name.
- An existing output produces a numbered copy and never an overwrite.

**What is not changed.** The counting loop, the confinement checks, the
template, and the layout engine. No existing generated output is touched.

## 3. AI captioning: guardrails and the approved workflow

### 3a. Already in place

**FACT**, each with evidence:

| Guardrail | Where |
|---|---|
| Key entered locally through Settings | `settings.save_key`, Settings screen |
| No key ships in the package | Key lives in `~/.rrf-app.env`; Section 10 excludes every env file |
| Only availability and last four reach Settings | `settings.status()` returns exactly `key_set` and `ends_with` |
| AI runs only after Mark asks | `POST /api/jobs/{name}/captions` fires from a button; nothing captions on open |
| Manual captions always available | Only blank captions are drafted; anything typed is left alone (`main.py:389,405`) |
| AI receives only selected photos | `photos_routes.included(manifest)` plus `_resolve_confined` per file (`main.py:386-394`) |
| AI receives only approved job context | `manifest.get("context")` and nothing else |
| No general filesystem access | Every path is resolved and confined to the job's `Photos` folder before opening |
| Cannot move, rename, edit, or delete sources | The AI path opens images read-only and writes only the app-owned manifest |
| AI never receives a full-size photograph | `captions.py:135-138` sends a 1024 pixel RGB JPEG made in memory. The original is never uploaded and never altered |
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
| Splitting | There is no splitting logic of any kind. One request, however many photos |

### 3c. The approved workflow

**APPROVED, 2026-08-18:**

**Sending.**

- Maximum 60 photos per AI-caption run.
- Show an `Estimated maximum cost` before sending, and the calculated cost
  from measured usage afterward. Both are defined in Section 3e.
- The estimate starts at **$0.05 per included photo** and moves with evidence,
  down or up, as measured runs accumulate. It is always shown as the
  arithmetic, not just a total.
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

**Why $0.05 is the starting figure and not a measurement.** It is a
deliberately conservative placeholder, and it is very likely higher than the
true per-photo cost. A 1024 pixel thumbnail runs roughly one to two thousand
input tokens, which at Opus-class input pricing lands nearer two cents than
five. Erring high is the safe direction for a number Mark reads before spending
money. Section 3e is how that guess stops being a guess.

### 3d. Split runs and partial failure

**FACT, 2026-08-18.** The 60-photo ceiling and the "one request when it fits"
rule cannot both hold at 60 photos. Sixty images at any realistic size exceed a
single provider request, so a full run will always split. The previous revision
of this plan did not say what happens when one group of a split run fails, and
that is money on the floor.

**APPROVED, 2026-08-18.** The 60-photo ceiling remains. When a run must be
split because of provider request-size constraints:

- Each successful group's captions save immediately as unreviewed drafts,
  before the next group is sent.
- If a later group fails, every earlier group's paid work is kept.
- Only the photos in the failed and unsent groups are left uncaptioned.
- The screen shows which photos remain without a caption.
- A deliberate `Retry remaining photos` action is offered.
- Nothing retries automatically.
- The retry estimate covers only the remaining photos, using the learned rate
  of Section 3e.
- Photos that already have a caption are never sent again and never charged
  again.
- Cost reporting distinguishes successful work from failed or unsent work. A
  split run aggregates every request belonging to that run, per Section 3e.
- Build remains governed by the per-photo review requirement in Section 3c.
  Remaining uncaptioned photos are handled by typing a caption or by excluding
  the photo, exactly as they are today.

**TEST, required before acceptance.** In `test_caption_guards.py` and
`test_caption_review.py`, all with a stand-in for the model so cost is zero:

- 60 photos is accepted; 61 refuses before any request is attempted.
- Failure before any group succeeds leaves every caption blank and reports
  plainly. Nothing is marked reviewed and nothing is charged.
- Failure after partial success keeps every successful caption as an unreviewed
  draft and names the remaining photos.
- A refresh after partial success still shows the successful captions.
- A deliberate retry sends only the remaining photos, and the count and
  arithmetic shown for that retry match only those photos.
- A photo that already carries a caption is never included in a retry payload.
- Retries are off at the client, so a failed request is attempted once.

### 3e. The adaptive cost estimate

**APPROVED, 2026-08-19.** The estimate is no longer a fixed figure. It starts
conservative and learns from measured usage. This closes the OPEN item the
previous revision left with the executor: post-run cost wording is now a
product decision, and it is made here.

**The starting prior.** The app begins as if it had already seen one expensive
run:

| Quantity | Value |
|---|---|
| Virtual photos | 60 |
| Rate per virtual photo | $0.05 |
| Total starting weight | $3.00 |

**The learned rate.**

```
learned rate = ($3.00 + cumulative calculated API cost)
               / (60 + cumulative successfully captioned photos)
```

With no evidence yet this is `$3.00 / 60`, which is `$0.05`, so the first run
uses exactly the arithmetic already approved. The prior is deliberately heavy,
so a single cheap run cannot swing the number far. Evidence moves it gradually.

**Before a run:**

- Multiply the learned rate by the number of included photos that will actually
  be sent. Photos that already carry a caption are not counted, because they
  are not sent.
- Round the displayed run total **upward** to the nearest $0.05.
- Label it **`Estimated maximum cost`**.
- Show the arithmetic, not just a total.

Worked examples, to make the behavior unambiguous:

| State | Learned rate | Photos sent | Displayed |
|---|---|---|---|
| No measured runs yet | $0.0500 | 12 | 12 x $0.0500 = $0.60 |
| No measured runs yet | $0.0500 | 60 | 60 x $0.0500 = $3.00 |
| After 12 photos measured at $0.24 | $0.0450 | 12 | 12 x $0.0450 = $0.54, shown as $0.55 |
| After a costlier run pulls it up | $0.0583 | 12 | 12 x $0.0583 = $0.70 |

The estimate may move **upward** if measured usage turns out more expensive.
Rounding is always upward, so the displayed figure is never lower than the
arithmetic behind it. That is why it is called a maximum and not a prediction.

**After a run:**

- Show **`Calculated API cost from measured usage`**.
- Also show measured input tokens, output tokens, and applicable cache tokens.
- **Do not call the dollar figure `actual cost`.** It is this app's arithmetic
  over a published price table, not a bill.
- **Anthropic's billing console remains the invoice authority.** The screen
  says so.
- A response carrying no usage information is recorded as **`Cost unavailable`**,
  never as `$0`.
- Unknown-cost requests never pull the learned rate downward. A missing number
  is not a cheap number.
- A split run aggregates every request belonging to that run into one run
  total.
- A deliberate retry is a **new run, linked to the original run**, covering only
  the remaining photos.

**Resetting the learning bucket.** Observations made under different conditions
are not comparable, so they are never mixed. A new bucket starts when any
cost-driving configuration changes:

- Model
- Published pricing
- Image-size or image-encoding settings
- Cache-pricing behavior

A new bucket restarts from the $3.00 over 60 prior. Prior buckets are retained
in the history of Section 3f and are never deleted, so an old rate can still be
inspected and recalculated.

**TEST, required before acceptance.** In `test_cost_estimate.py`, all with a
stand-in for the model so cost is zero:

- The first run uses the full $0.05 prior.
- The estimate declines gradually after cheaper measured runs, and the decline
  matches the formula rather than jumping to the last observed rate.
- The estimate increases after more expensive runs.
- The displayed run total rounds upward to the nearest $0.05.
- A split run aggregates every request into one run total.
- Partial success counts only successfully captioned photos in the denominator.
- A retry is recorded as a new run linked to its original.
- A response with no usage is recorded as `Cost unavailable`.
- An unknown cost never counts as zero and never lowers the learned rate.
- Changing the model creates a new learning bucket.
- Changing the pricing table creates a new learning bucket.
- Changing image settings creates a new learning bucket.

### 3f. Local AI Usage History

**APPROVED, 2026-08-19.** The app keeps its own local record of AI runs, so the
learned rate can be audited and recalculated rather than trusted.

**Where it lives.** App-owned local state, outside every job folder, alongside
the other app-owned files of Section 6 and written with the same atomic helper.
Nothing about it is ever written into one of Mark's folders.

**What each run record holds, and nothing more:**

- Local run ID
- Parent run ID, when the run is a deliberate retry
- Timestamp
- Model identifier
- Pricing-table version and the effective rates used
- Image-settings version
- Number of photos requested
- Number successfully captioned
- Number remaining or failed
- Number of API requests
- Status: completed, partial, failed, or cost-unavailable
- Pre-run estimate
- Per-request input, output, and applicable cache-token usage
- Per-request calculated cost, when available
- Total calculated run cost, when available
- Learned rate after the run

**What it must never hold. This is the privacy boundary and it is a
requirement, not a preference:**

- No job names
- No addresses
- No photo filenames
- No images
- No captions
- No prompts
- No API keys
- No client content of any kind

A cost audit needs counts, tokens, and rates. It does not need to know what the
photographs were of, and a file that knows costs nothing to leak only because
it does not know.

**Retention.** The app retains the underlying run records, not only the current
average, so Spenser can inspect them and recalculate later. Recording the
pricing-table version and the image-settings version on every run is what makes
a recalculation meaningful afterward.

**TEST, required before acceptance.** In `test_usage_history.py`:

- A run record round-trips with every field above.
- A retry record carries its parent run ID.
- The learned rate stored on a run reproduces from that run's own fields.
- The history survives an upgrade and a rollback, tested separately.
- **No job name, address, photo filename, caption, prompt, image, or key
  appears anywhere in the written file.** Asserted by scanning the file's bytes
  for values known to be present in the test job.
- A cost-unavailable run is stored as unavailable and is excluded from the
  learned-rate arithmetic.
- Records from a prior learning bucket are retained after a bucket reset.

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
retry from Sections 3c and 3d, with no automatic retry burning further calls.
That is the intended behavior, not a gap.

### 4a. Two different network failures currently read differently

**FACT, 2026-08-18.** Saving a key and drafting captions do not fail the same
way, and only one of them was written to degrade well.

- Saving a key catches every non-authentication exception and stores the key
  anyway, with "Saved, but we could not reach Anthropic to check it."
  (`main.py:311-314`). A blocked network, a captive proxy, and a TLS-inspecting
  corporate proxy all land here and read sensibly.
- Drafting captions has no equivalent. Whatever the SDK raises is what
  surfaces.

So a blocked network does not produce the same clear message as a missing key.
It produces a worse one, on the caption path only. That was an OPEN question in
the previous revision. It is now answered and it is a defect to fix.

**DIRECTION, 2026-08-18.** Caption failures are reported in plain language,
naming which of these happened, without a traceback and without raw SDK text:

- No key configured. Already handled; captions turn themselves off and say so.
- The key was refused.
- Anthropic could not be reached at all.
- Anthropic was reached and refused the request, for example a spending limit.
- The request was too large and could not be split further.

**TEST.** Each of the five paths above produces its own plain sentence, with a
stand-in for the model. No test uses a real key or makes a real request.

## 5. Version identity, ports, and update direction

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

**FACT, 2026-08-18.** No version string exists anywhere in the app today. Not
in `main.py`, not in `run_app.py`, not in `app/web/package.json`, which carries
`name`, `private`, and `type` and no `version` field. Showing a version on
every screen is entirely new work.

### 5a. Version identity

**DIRECTION, approved 2026-08-18. Not built, not proven.**

- A `VERSION` file sits at the package root and holds the version string.
- A permanent `GET /api/version` endpoint returns the running version.
- Shared screen furniture renders it on every screen.
- The launcher uses `/api/version`, and never `/api/demo`, to identify the app.
- Demo code and demo routes remain excluded from the shipped package, per
  Section 10.

**Why this replaced the previous proposal.** The previous revision had the
launcher probe `/api/demo` and treat a JSON answer as "our app is up". Section
10 removes `demo.py` and both demo routes from the package, so on Mark's
machine that probe returns 404 and never JSON. The probe would have worked on
Spenser's Mac and failed only on the machine that matters. `/api/version` is
the correct probe because it is required by the approved version display
anyway, it is never excluded, and unlike `/api/demo` it says *which* version
answered.

### 5b. Port and single instance

**FACT, 2026-08-18.** `run_app.py:13` hardcodes port 8000. `busy.py:31` is a
`threading.Lock`, so it guards writes inside one process and nothing across
two. Two app processes writing `~/.rrf-app.json` and
`~/.rrf-classifications.json` are unguarded.

**DIRECTION, approved 2026-08-18. Not built, not proven.**

- Bind to port `0` and let Windows select a free local port.
- Keep the server bound to `127.0.0.1`, never `0.0.0.0`.
- Record the chosen port in that version folder's own `runtime.json`, beside
  the launcher. It is created at runtime, is not part of the packaged set, and
  is outside the immutable manifest and aggregate. Section 11 says why.
- Open the browser at the port actually bound, never at an assumed port.
- Before starting, inspect sibling version folders for a live RRF process, by
  reading each `runtime.json` and probing the port it names. A sibling that has
  never been started has no `runtime.json`, which counts as not running.
- The launcher must never accept another version's `/api/version` response as
  success.
- If another version is running, refuse to start and show a plain message
  naming the running version and its folder.
- Do not allow two versions to run simultaneously.
- Do not use an unbounded port walk-up.

**Why this replaced the previous proposal.** Two reasons, and both were live
defects rather than preferences.

First, a version-blind probe breaks upgrade and rollback in both directions. If
v2 is running and Mark double-clicks v1 to roll back, he gets v2. If v1 is
running and he double-clicks v2 to upgrade, he gets v1. Both look like success,
and the only clue is a version number nobody asked him to read.

Second, the previous alternative, walking up from 8000 to the first free port,
starts a second copy instead. Given `busy.py:31` that is not benign. It also
has no terminating condition if a security product answers on every local port.
Binding port 0 removes the walk-up loop entirely, makes versioned folders
genuinely independent, and turns "am I already running" into a precise question
answered by this version's own `runtime.json`.

**UNPROVEN.** That Windows selects a usable loopback port under `bind(0)` on
Mark's machine, that `runtime.json` is writable inside the package folder where
he unzipped it, and that the sibling scan sees folders he may have moved or
renamed. All three are Windows acceptance items.

**TEST, on the Mac, in `test_launcher.py`:**

- Binding port 0 yields a bound port and the browser target uses that port.
- `runtime.json` is written with the bound port and is re-read correctly.
- A sibling folder reporting a live port of a *different* version causes a
  refusal, and the message names that version.
- A sibling folder reporting a stale port that answers nothing does not cause a
  refusal.
- A port that answers but does not return this app's `/api/version` shape is
  never treated as success.
- A port that answers with a *different* version's string is never treated as
  success.
- There is no unbounded loop: interference on every probed port produces a
  bounded, plain refusal rather than a hang. See Section 20.

### 5c. Last-known-good

**APPROVED product requirement:** the last successfully started version is
recorded in app-owned settings.

**DIRECTION, approved 2026-08-18. Not built, not proven.**

- The record lives in its own file, `~/.rrf-app-version.json`.
- It does **not** live inside `~/.rrf-app.json`.
- A version counts as successfully started only when both hold:
  1. `GET /api/version` on the bound port returns that exact version string.
  2. The same process is still alive 20 seconds later.
- The running server records that evidence itself, after the 20-second check,
  not the launcher.
- The record is diagnostic evidence for Spenser. Nothing consumes it
  automatically.
- Do not implement automatic rollback.
- Rollback stays manual: close the current version, then launch the prior
  version's folder.

**Why the record moved out of `~/.rrf-app.json`.** That file is written every
time Mark picks a folder or edits his active job list, it is written
non-atomically (`workspace.py:56-62`), and a read failure returns empty
silently (`workspace.py:48-52`). Putting the crash-recovery record inside the
file most likely to be damaged by a crash is backwards. The previous revision
chose it for "fewer files to migrate", which is the convenience argument and
the weaker one. A fourth file is not meaningfully harder to keep stable, and
the test asserting literal filenames covers four as easily as three.

**Why the threshold is what it is.** Five weaker meanings of "started
successfully" were considered and rejected:

| Candidate meaning | Why it is not enough |
|---|---|
| The process started | A missing wheel makes the process start and die a second later |
| The socket bound | Binding proves nothing about whether the app is importable |
| The server answered one request | Another program answering on that port would be recorded as our success |
| The browser opened and rendered | Not observable. Nothing reports back what the browser did |
| Mark completed a real task | The honest meaning of good, but nothing in the app knows it and he would never confirm it |

The version check is what stops another program's answer from counting. The
20-second wait is what handles the case the requirement exists for, a version
that starts and then fails: a lazily failing import, a missing template, or a
crash on first work all surface inside that window. Longer risks Mark closing
the window before the record is written; shorter sits inside the window where a
lazy import failure is still pending.

Writing it from the server rather than the launcher matters, because a launcher
that exits after opening the browser cannot observe anything afterward, and
would record a success it did not witness.

**TEST, in `test_settings_survive_upgrade.py`:**

- The four home-folder filenames are asserted as literals.
- The last-good record round-trips.
- A version answering `/api/version` with a different string never records
  itself as good.
- A process that exits before the 20-second mark never writes the record.
- The record survives an upgrade and a rollback, both tested separately.

## 6. Safe app-owned state

**FACT, 2026-08-18.** The three existing home-folder files do not behave the
same way, and the difference is not deliberate.

| Path | Holds | Written by | Written how |
|---|---|---|---|
| `~/.rrf-app.env` | The Anthropic API key, mode 0600 where the OS supports it | `settings.py:38-47` | Direct `write_text`. No temporary file. No explicit encoding on read or write (`settings.py:35,41`) |
| `~/.rrf-app.json` | The chosen jobs folder and the active job list | `workspace.py:23,35-39` | Direct `write_text`, encoding stated (`workspace.py:61`) |
| `~/.rrf-classifications.json` | What Mark said each file is | `classify.py:46` | Temporary file then `os.replace` (`classify.py:63-79`). The only safe one |

All resolve through `Path.home()` and all are overridable by environment
variable for tests. None sits inside the repository or inside a job folder.

**UNPROVEN.** That `Path.home()` resolves to Mark's Windows profile. The code
fact is `Path.home()`. Where it lands on his machine is a Windows acceptance
item, and the previous revision recorded it inside a FACT table, which was
wrong.

**FACT.** An unreadable settings file is currently treated as no settings at
all, with no message (`workspace.py:48-52`). The comment there argues that
asking Mark again costs ten seconds. That reasoning holds for a file that was
never written. It does not hold for a file that was written and then damaged,
where the same silence looks to him exactly like the app forgetting his setup.

**DIRECTION, approved 2026-08-18. Not built, not proven.**

- One shared atomic-write helper: write a temporary file in the same folder,
  then `os.replace`. Lifted from `classify.py:63-79`, which already does it.
- Apply it to all four: workspace settings, API-key configuration,
  classifications, and last-known-good state.
- Add a simple schema-version field to each structured JSON state file, so a
  future version can refuse a file it does not understand rather than misread
  it. One integer, not a migration framework.
- A malformed or unreadable settings file produces a clear, recoverable error
  naming the file and what to do, instead of silently behaving like first-time
  setup.
- Original job files and client files remain untouched by all of it. None of
  this writes anything into one of Mark's folders.

**TEST, required before acceptance:**

- Interruption during a write leaves the previous file intact and readable, for
  each of the four files.
- A truncated or malformed file produces the clear recoverable error, and is
  never mistaken for first-time setup.
- A file carrying an unknown schema version is refused with a plain message
  rather than misread.
- Upgrade survival and rollback survival are tested **separately**, not as one
  case, for each of the four files.
- A fingerprint of the job folder before and after every state operation proves
  no job file or client file was written, moved, renamed, or deleted.

## 7. Runtime, dependencies, and the Task 1 evidence

### 7a. What Task 1 proved

**FACT, 2026-08-19, from Task 1.** Evidence gathered on the Mac from the
package index and python.org. Task 1 changed no repository file, installed
nothing, and made no API call.

- **Every pinned dependency resolves to binary `win_amd64` wheels for CPython
  3.9, 3.10, 3.11, 3.12, 3.13, and 3.14.** 34 distributions on 3.9 and 3.10,
  33 on 3.11 and above. The difference is `typing-extensions`, required only
  below 3.11.
- **No source build is required on any candidate.** Resolution was performed
  with binary artifacts only, so a source fallback could never make a
  candidate appear viable.
- **`pillow-heif==1.1.1` publishes a compatible Windows wheel for every
  candidate checked.** 53 files published, 8 `win_amd64` wheels, 6 CPython and
  2 PyPy.

  | Candidate | ABI | Wheel |
  |---|---|---|
  | 3.9 | cp39 | `pillow_heif-1.1.1-cp39-cp39-win_amd64.whl` |
  | 3.10 | cp310 | `pillow_heif-1.1.1-cp310-cp310-win_amd64.whl` |
  | 3.11 | cp311 | `pillow_heif-1.1.1-cp311-cp311-win_amd64.whl` |
  | 3.12 | cp312 | `pillow_heif-1.1.1-cp312-cp312-win_amd64.whl` |
  | 3.13 | cp313 | `pillow_heif-1.1.1-cp313-cp313-win_amd64.whl` |
  | 3.14 | cp314 | `pillow_heif-1.1.1-cp314-cp314-win_amd64.whl` |

- **HEIC remains in scope.** The riskiest pin turned out to be the
  best-covered one. No product compromise was needed and none was made.
- **`uvloop` is correctly excluded on Windows.** Its own marker,
  `sys_platform != "win32" and ... and extra == "standard"`, evaluates false
  under a Windows CPython environment. It is absent from every candidate's
  resolution. A first attempt appeared to fail on `uvloop`, which was the
  development Mac's pip evaluating markers against the running platform, not a
  Windows fact.
- **`colorama` is included on Windows.** Its marker is
  `sys_platform == "win32" and extra == "standard"`, so Windows gains a
  dependency the Mac does not have. Earlier revisions of this plan never
  mentioned it.
- **The existing suite remained green: 320 passed, 15 skipped.** Matching the
  branch-point baseline in Section 17 exactly.
- **Task 1 changed no repository file.** `git status --short` empty and the
  tree identical to HEAD at the end of the task.

**FACT. Wheel availability does not prove Windows import success.** Everything
in 7a is artifact evidence gathered on a Mac. It says a compatible file exists
and can be fetched. It says nothing about whether that file loads on Mark's
machine.

**UNPROVEN until Gate A**, and none of it may be reported as working before
then: that the embeddable runtime starts at all; that its `._pth` honours a
packaged `site-packages`; that the compiled wheels import; that real HEIC
decoding works there; that `Path.home()` resolves to his profile; that dynamic
port binding yields a usable loopback port; what SmartScreen actually says; and
that a second version is refused rather than started.

### 7b. The approved runtime direction

**APPROVED, 2026-08-19. CPython 3.14 is the pilot runtime direction.** The
runtime version is no longer an open question. Any earlier wording in this
document that treated it as unresolved is superseded by this subsection.

- **Target artifact, verified by Task 1:** `python-3.14.7-embed-amd64.zip`,
  from `https://www.python.org/ftp/python/3.14.7/`. HTTP 200, 12,673,227 bytes.
- **All nine compiled dependencies currently publish compatible `cp314`
  wheels**, all native, with no `abi3` fallback and no source artifact.

**The selection rests on current Windows binary support and the longer
remaining bugfix window, not on 3.14 being newer.** Task 1 measured a fact that
decides it: python.org stops publishing Windows embeddable builds when a series
leaves bugfix support and goes security-only.

| Series | Last release with an embeddable | Security releases published since, with no Windows binary |
|---|---|---|
| 3.9 | 3.9.13 | 12 |
| 3.10 | 3.10.11 | 10 |
| 3.11 | 3.11.9 | 7 |
| 3.12 | 3.12.10 | 4 |
| 3.13 | 3.13.15 | none, still current |
| 3.14 | 3.14.7 | none, still current |

So shipping 3.12 would ship a CPython missing four rounds of security fixes,
and 3.9 would miss twelve. Only 3.13 and 3.14 are current. Between those two,
3.13 leaves bugfix support around October 2026 and its embeddable then freezes
exactly as 3.12's already has, while 3.14 keeps receiving Windows binaries to
roughly October 2027. The pilot carries versions 1 through 6 and the folder
sits on Mark's machine for months, so the runtime that keeps being patched is
the stronger one.

The argument against 3.14 is ecosystem youth. Task 1 checked it rather than
dismissing it: all nine compiled dependencies already ship native `cp314`
wheels today. The residual risk is a future pin bump, not the present set.

**Real imports remain unproven until the Windows spike.** Approving the
direction is not evidence that it runs.

**If the Windows spike fails, stop and return evidence. Do not silently change
the runtime.** Changing it is a product decision and it is not the executor's.

### 7c. What actually ships, corrected

**FACT, 2026-08-19, from Task 1. An earlier revision of this plan was wrong
about `httpx`.** It said "pytest and httpx are test-only and are not installed
into the package". That is false for `httpx`.

- `anthropic==0.121.0` requires `httpx<1,>=0.25.0` **unconditionally**, with no
  marker and no extra.
- **The shipped package must therefore include `httpx`, `httpcore`, `certifi`,
  `idna`, and `anyio`.**
- Uncorrected, the packaging script would omit them and `import anthropic`
  would fail on Mark's machine and nowhere else.
- **`pytest` remains test-only and does not ship.**

**FACT. The compiled Windows dependency set contains nine packages**, not the
three an earlier revision named:

| Compiled package | Arrives via |
|---|---|
| Pillow | direct pin |
| pillow-heif | direct pin |
| pydantic-core | pydantic |
| lxml | python-docx |
| jiter | anthropic |
| httptools | uvicorn[standard] |
| watchfiles | uvicorn[standard] |
| websockets | uvicorn[standard] |
| PyYAML | uvicorn[standard] |

**DIRECTION, approved 2026-08-19.**

- **Packaging and Gate A tests must import and verify the complete runtime
  dependency closure**, not only the packages previously named by hand.
- **The committed packaging script must derive the runtime dependency closure
  from the pinned requirements and the resolved metadata**, rather than
  maintaining a hand-written copy of the list. A hand-written list is how
  `httpx` went missing, and a second hand-written list would fail the same way
  in a new place.

**TEST. Gate A must import the whole closure on Windows**, not a sample. At
minimum `anthropic` and every distribution it pulls, plus `uvicorn`, `PIL`,
`pillow_heif`, `docx`, `lxml`, and `pydantic_core`.

### 7d. What is still to be proven, and in what order

The seven proofs, with Task 1's two now closed:

1. **Download the targeted Windows wheels without installing them.**
   **DONE in Task 1.** Passed for all six candidates.
2. **Assemble the self-contained runtime through the committed packaging
   script** of Section 11. Not started.
3. **On Windows, import the complete runtime dependency closure**, per 7c.
   Not started.
4. **Verify `Path.home()` resolves to the expected Windows user profile.**
5. **Verify direct HEIC files open correctly.** A `.heic` placed straight into
   a `Photos` folder, not uploaded through the app. Per Section 1b this fails
   today, so this test starts red and proves Section 12 fixed it.
6. **Verify Word opens the generated document.**
7. **Verify the chosen runtime configuration and `._pth` behavior** rather than
   assuming them. Task 1 proved artifacts exist; it proved nothing about the
   import path. This stays a Windows observation.

**If HEIC support fails on Windows, stop and return evidence.** Do not silently
remove HEIC support and do not silently change runtime versions.

## 8. How the built web interface enters the package

**DIRECTION, approved 2026-08-18.** `app/web/dist` is produced on the Mac by
`cd app/web && npm ci && npm run build` and copied into the package as
`app/web/dist`. Nothing else from `app/web` ships: no `src`, no
`node_modules`, no `package.json`. Mark never has Node, and the packaging
script fails loudly if `dist` is missing or older than `src`, rather than
shipping a stale interface.

**FACT.** `main.py:522` already resolves `dist` relative to the server file, so
the mount works unchanged inside a package laid out this way.

## 9. The Windows launcher

**DIRECTION, approved 2026-08-18. Not built, not proven.** The logic lives in
Python and the `.bat` is a thin shim. `HOW-WE-WORK.md` says nothing but Python
runs on Mark's machine, and a port check written twice, once in bash and once
in batch, is a defect waiting to happen. So `run_app.py` grows the startup
logic and both platforms share it.

`Start Roy R. Fisher.bat` does three things: change to its own folder, run
`python\python.exe app\run_app.py`, and `pause` on failure so the window stays
open with the reason visible.

`run_app.py` gains, in order:

1. **Verify the immutable package before importing any third-party
   dependency.** The manifest check of Section 11, in standard-library Python
   only, and before `runtime.json` exists or is touched. A missing, truncated,
   moved, or corrupt file is named in plain language and the app does not
   start. This is first because `run_app.py:7` imports uvicorn at module scope
   today, so a damaged package currently produces a traceback before any of our
   code can speak.
2. **Refuse if another version is running.** The sibling scan of Section 5b.
   The message names the running version and its folder.
3. **Detect this same version already running.** Read this folder's own
   `runtime.json`, probe that port, and confirm `/api/version` returns this
   exact version. If it does, open the browser at that port and exit 0 without
   starting a second copy. A different version, or an answer that is not ours,
   is never accepted as success.
4. **Bind port 0 and record it.** Write the bound port to this folder's
   `runtime.json`, creating it if this is the first start. This happens only
   after step 1 passed, and `runtime.json` is outside the immutable set, so
   writing it can never invalidate the package. Never assume 8000. Never walk
   up.
5. **Start, then wait for a real answer.** **FACT:** today the browser opens on
   a one-second timer (`run_app.py:12`), which is a guess. Instead poll
   `/api/version` on the bound port until it answers with this version, up to a
   bounded timeout, then open the browser. That is the whole of "never open a
   dead browser page".
6. **Record last-known-good after 20 seconds.** Section 5c. From the server, not
   from here.
7. **Report failure in plain words.** If the server never answers within the
   timeout, print what was tried, the port, and what to do next, then exit
   non-zero so the `.bat`'s `pause` holds the window open. No traceback as the
   only output.

The Mac `.command` is reduced to the same thin shim so both platforms take the
same path.

**Keep the console visible during the pilot.** A hidden console makes failure
invisible, and the console is the only place a plain failure message can land.
This is a pilot decision, revisited later.

## 10. Package contents and exclusions

**DIRECTION for the layout, approved 2026-08-18.** One versioned top folder so
nothing overwrites a prior pilot:

The freshly built package, exactly as it leaves the packaging script. Every
file here is immutable:

```
Roy R. Fisher v0.1.0/
    Start Roy R. Fisher.bat
    README FIRST.txt          plain instructions for Mark
    VERSION                   the version string, read and shown on every screen
    MANIFEST                  immutable file list with sizes, plus the aggregate hash
    python/                   embedded runtime + site-packages
    app/
        run_app.py
        data/  engine/  server/  templates/
        web/dist/
```

**`runtime.json` is not in that tree.** It does not exist in a freshly built
package. It is created at runtime inside the version folder, and only after
immutable package validation has already succeeded. It is mutable by design,
it is excluded from the manifest and from the aggregate hash, and Section 11
says why that separation matters.

**Included, and all immutable:** `run_app.py`, `app/data`, `app/engine`,
`app/server`, `app/templates`, `app/web/dist`, the embedded runtime, the
launcher, the readme, the version file, the manifest.

The embedded runtime carries **the complete runtime dependency closure** of
Section 7c, derived by the packaging script from the pinned requirements and
resolved metadata. That closure includes `httpx`, `httpcore`, `certifi`,
`idna`, and `anyio`, which an earlier revision wrongly called test-only. It
excludes `pytest`, which genuinely is.

**Excluded. The exclusion list itself is not a proposal: it is a requirement,
and every line is asserted by a packaging test.**

- `app/tests` and every test artifact
- `app/web/src`, `app/web/node_modules`, `package.json`, `package-lock.json`
- `app/server/demo.py` and both demo routes (development-only control)
- `RRF Demo Jobs/` and any demo or client material
- `brand/`, `docs/`, `.git/`, and anything from `Report Examples/` or `locker/`
- `__pycache__/`, `.pytest_cache/`, `.DS_Store`
- any `.env` file, any key, any cache, any thumbnail cache
- `Start Roy R. Fisher.command` (the Mac launcher)
- `runtime.json` (created at runtime, never packaged, never hashed)

### 10a. Removing demo.py correctly

**FACT, 2026-08-18.** `demo.py` cannot simply be deleted from the package.
`main.py:14` imports it unconditionally, and `main.py:98` references
`demo.DemoError` inside an exception-handler decorator. Deleting the file makes
the server fail to import at all, so the app would not start on Mark's machine.

**DIRECTION, approved 2026-08-18.** Do not delete `demo.py` without also
handling its imports and its exception reference:

- Import it conditionally.
- Register neither demo route when it is absent.
- Do not register the `demo.DemoError` exception handler when it is absent.

**FACT.** `demo.enabled()` already gates the reset (`main.py:120-125`), so
absence from the package is defence in depth: the control is gated and also
not present. And `App.jsx:27` already tolerates a missing route, so no screen
breaks.

**TEST.** A packaged tree with `demo.py` absent imports, starts, serves
`/api/version`, and renders every screen. This test runs against output from
the packaging script, per Section 11.

## 11. Reproducible packaging and integrity check

**FACT, 2026-08-18.** There is no packaging tooling of any kind in the
repository. The previous revision described assembly as four commands typed by
hand, and proposed a test asserting "against a built package tree" without
naming anything that builds it. A test that checks an artifact no script
produces is a test that gets run once.

**FACT, 2026-08-19.** The previous revision put mutable `runtime.json` inside
the package while also describing the package as manifest-checked and hashed,
and it never said how the manifest avoids hashing itself. Both are
contradictions: on the first normal startup the app would have invalidated its
own package, and a manifest that contains its own hash cannot be computed.

**DIRECTION, approved 2026-08-19. Not built, not proven.**

**The immutable set.** Every packaged file is immutable. Exactly two things are
outside the immutable set:

| Outside the set | Why |
|---|---|
| `runtime.json` | Created at runtime, after validation succeeds. Holds the bound port. Never packaged, never listed, never hashed |
| `MANIFEST` itself | A file cannot contain a hash of itself. It is excluded from its own aggregate |

- Package creation is performed by a **committed, repeatable packaging
  script**, not by manual commands.
- **The script derives the runtime dependency closure from the pinned
  requirements and the resolved metadata.** It never carries a hand-written
  copy of the dependency list. Section 7c records what a hand-written list
  already cost: `httpx` was called test-only and would have been omitted.
- The script generates the manifest during packaging, listing every **immutable**
  file and its size.
- The aggregate is defined **deterministically over the ordered paths, sizes,
  and contents of all immutable packaged files**. Ordered, so two machines
  produce the same value. Paths and sizes as well as contents, so a file moved
  or truncated changes the aggregate even when the bytes elsewhere match.
- The launcher recomputes that aggregate over the immutable files and compares
  it with the value stored in the manifest.
- Validation runs **before importing any third-party dependency**, per Section 9
  step 1, and before `runtime.json` is created.
- **Validation must not reject the package merely because `runtime.json` was
  created or updated during normal use.** That is the whole reason it sits
  outside the set.
- Missing files, unexpected immutable-file size changes, and same-size byte
  corruption all produce a plain-language error naming the problem and the file.
- **Mark performs no manual checksum comparison.** The check is the launcher's
  job, never his. A checksum he is asked to compare is a second step on his
  machine, which the roadmap calls a defect. A checksum nobody checks is
  decoration. The launcher doing it himself is neither.
- Running the packaging script twice from identical inputs must produce the
  same immutable manifest.
- The console stays visible during the pilot so those messages are readable.

**What this check honestly does, and does not do.** It detects damaged or
incomplete packages: an interrupted extraction, a truncated download, a
corrupted file, a missing file. That is what it is for and it does that well.

Without code signing it does **not** prove publisher identity, and it does
**not** protect against deliberate replacement of both the files and the
manifest together. Anyone able to rewrite the package can rewrite the manifest
beside it. This is an integrity check against accident, not a security control
against an adversary. Code signing is out for this pilot by decision, so that
exposure is accepted and named rather than papered over.

**Not in this pilot, by decision:** no MSI, no registry integration, no Windows
service, no automatic updater, no automatic rollback, no code signing.

**Why sizes plus one aggregate, and not a hash per file.** A package with an
embedded runtime holds thousands of `site-packages` files. Per-file hashing
would make every startup slow for no added protection that matters here. Sizes
catch truncation, which is what an interrupted extraction produces. The
aggregate over ordered paths, sizes, and contents catches the rest, including
corruption that preserves file size.

**TEST, required before acceptance.**

- `test_package_manifest.py` runs **against output produced by the committed
  packaging script**, never against a hand-assembled tree.
- The manifest includes every required path from Section 10.
- The manifest excludes every path in the Section 10 exclusion list, asserted
  line by line.
- The manifest does not list `runtime.json`.
- The manifest does not list itself, and the aggregate excludes itself.
- A freshly built package validates.
- **The same package still validates after a normal startup has created
  `runtime.json`, and again after a second startup has updated it.**
- A deliberately truncated immutable file is detected and named.
- A deliberately missing immutable file is detected and named.
- A byte-level corruption of an immutable file that preserves its size is
  detected.
- A file moved to a different path within the package is detected.
- Validation happens before any third-party import, proven by removing a
  required wheel and confirming the plain message appears rather than an
  `ImportError` traceback.
- Running the packaging script twice from identical inputs produces an
  identical immutable manifest, aggregate included.
- The packaged closure contains every distribution the pinned requirements
  resolve to, `httpx` and its chain included, and contains no test-only
  distribution.
- Removing any single distribution from the closure is detected before the
  package is declared good.

## 12. Report photo optimization

**FACT, 2026-08-18.** The document builder embeds the original image file.
`photo_pages.py:75` calls `add_picture(str(image_path), width=Inches(4.0))`.
python-docx stores the file's own bytes inside the `.docx` package and the
`width` argument sets only the displayed size in the document XML. A 6 MB phone
photograph displayed at four inches is still 6 MB inside the document.

**FACT.** The two existing downscale paths do not help, because neither touches
the document:

| Path | What it makes | Where it goes |
|---|---|---|
| AI captioning | 1024 px RGB JPEG, quality 85, in memory | Sent to the model. Never written to disk, never used by the builder (`captions.py:135-138`) |
| Screen thumbnails | `THUMB_PX` = 1024 JPEG, quality 85 | The app's own thumbnail cache, for the browser only (`photos.py:429-431`, `photos.py:28`) |
| HEIC upload conversion | Full-resolution JPEG, quality 92 | Written into the `Photos` folder, and only on the upload route (`photos.py:230-235`). Photos Mark copies in himself never pass through it |

So the AI thumbnail is already separate and does not solve Word or PDF size.

**APPROVED, 2026-08-18. The originals are never touched.**

- Never modify, replace, rename, move, or recompress an original photograph.
- Create temporary optimized copies solely for document assembly.
- Apply EXIF orientation before resizing.
- Convert embedded report copies to RGB JPEG.
- Limit the longest edge to 1,600 pixels.
- Use JPEG quality 85.
- Never enlarge a smaller image.
- Use the optimized copies in the generated Word document.
- Remove temporary copies after a successful build and after a failed one.
- HEIC, JPEG, and photographic PNG inputs all follow the same
  document-optimization path.
- Existing output collision protection remains in force, per Section 2.

**FACT, worth stating plainly.** Nothing in the app path applies EXIF
orientation today. `photo_pages.exif_order` reads `DateTimeOriginal` for
ordering (`photo_pages.py:37-51`) and never reads the orientation tag, and
grep finds no `exif_transpose` anywhere in `app/server` or `app/engine`. So
applying orientation before resizing is new behavior, not a restatement of
something already happening. A rotated phone photograph may therefore appear
differently in the built document after this change than before it, and that
difference is a correction.

**This also fixes the live defect in Section 1b.** Converting the document copy
to RGB JPEG makes a directly-placed HEIC embeddable, because python-docx will
then be handed a JPEG it recognises rather than a HEIC it does not.

**TEST. The acceptance plan must:**

- Fingerprint every original photograph before and after building, and prove
  each one is byte-for-byte unchanged. This is the first test, not the last.
- Prove no original was renamed, moved, or deleted, and that the temporary
  copies are gone after a successful build and after a failed one.
- Compare generated DOCX size before and after optimization, and record both.
- Open the DOCX in Windows Word.
- Export or save the document to PDF through the available Windows Word
  workflow, and record the PDF size.
- Visually compare representative photographs in Word and in the PDF against
  the originals.
- Cover landscape, portrait, rotated EXIF, HEIC, JPEG, PNG, small images, and
  very large phone photographs.
- Treat visual acceptance and measured file size as **separate evidence**. A
  smaller file is not a claim about how it looks.
- **Do not claim "no visible quality loss" until Spenser completes the screen
  review.** Measured size may be reported before then. Appearance may not.

**A note on the PDF step.** Producing a PDF here is Mark saving from his own
Word by hand, as part of acceptance. It is not the Office bridge, it is not
COM automation, and it says nothing about Phase 1. It exists only to measure
what the optimization does to a delivered-shaped file.

## 13. Representing unfinished features honestly

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

**DIRECTION for the smallest placement, approved 2026-08-18.** One band at the
bottom of the job screen (`JobHome.jsx`), below the folder bands, titled
`Planned workflows`, holding one plain non-interactive row. Reasons: the job
screen is the one screen Mark returns to, the folder bands above it already
establish the band pattern, and a row there cannot be confused with an action
because the actions on that screen sit at the top on the title's row, per
`HOW-WE-WORK.md`. No new route and no new screen. Not implemented in this
checkpoint.

## 14. Delivery to Mark

**APPROVED, 2026-08-18.** The pilot package reaches Mark through a **private
download link**.

**Why this matters technically, and is not just logistics.** A zip downloaded
through a browser carries the Mark of the Web, and Windows propagates that
marking to the files extracted from it. An unsigned `.bat` extracted from a
marked zip is the case most likely to be stopped by SmartScreen. A package
copied from a shared folder or a USB stick usually carries no such marking, so
testing that way would pass while the real path fails.

**TEST. The acceptance test uses the same delivery path Mark will use:**

- Download through a browser on Windows.
- Extract with Windows Explorer's own built-in extraction.
- Preserve the real Mark-of-the-Web and SmartScreen behavior. Do not strip the
  marking, do not unblock the zip first, and do not extract with a third-party
  tool that behaves differently.
- **Do not test only through a shared folder or a USB path that avoids the real
  download behavior.** Such a test proves nothing about what Mark will see.
- Record the exact prompts Mark sees, word for word, including which button is
  hidden behind "More info".
- Spenser is present by screen share for the first installation.
- **One SmartScreen confirmation is acceptable for this pilot only.** It is a
  knowing exception to the "anything that needs two steps on his machine is a
  defect" rule, taken because code signing is out for this pilot.
- Reconsider code signing before any wider distribution.

## 15. The testing ground

**APPROVED, 2026-08-18.** A repeatable acceptance environment, in this order:

1. Begin with a disposable synthetic job containing safe test photos.
2. Test a normal 12-photo run.
3. Test the 60-photo maximum.
4. Confirm 61 photos are blocked before any API request or any cost occurs.
5. Never test against original evidence or client folders.
6. A copied real demo job may be used only after Spenser selects the copy and
   explicitly authorizes those photos for an external AI request. Since
   2026-08-19 that authorization has a mechanism rather than a convention: the
   job must be on the AI-safe allowlist of Section 25b, and everything else
   under the demo root is refused in code before a client is built.
7. Generated documents must use fresh output names and must not overwrite
   existing documents.

**How the block at 61 is proven without spending anything.** The ceiling is
checked before the client is constructed, so the refusal path never reaches the
network. The test asserts the refusal and asserts that no request was
attempted, using a stand-in for the model per `HOW-WE-WORK.md`'s list of three
external conditions that may be stood in for. Cost of that test: zero.

**Synthetic photos.** Generated with Pillow, the way
`test_shipped_template.py` already does. They prove the mechanics of counting,
batching, refusing, reviewing, naming, and optimizing. **They prove nothing
about caption quality**, which needs real photographs and is why item 6 exists.
They also prove nothing about how an optimized photograph looks, which is why
Section 12 requires Spenser's screen review on real images.

## 16. Acceptance checklist

**APPROVED, 2026-08-18.** The pilot is not proven until every one passes.

**Installation and startup**

1. Clean installation and first launch, through the Section 14 delivery path.
2. The exact SmartScreen and Mark-of-the-Web prompts, recorded word for word.
3. Package validation catches a truncated file and names it in plain language.
3a. The package still validates after normal startup has created and then
    updated `runtime.json`.
4. Visible version number on every screen, matching the folder launched.
5. Launching a second version while one runs is **refused**, and the message
   names the running version.
6. Jobs-folder selection.

**Captions**

7. API-key setup, and behavior with no key present.
8. `Estimated maximum cost` shown before the request, with its arithmetic.
9. `Calculated API cost from measured usage` shown afterward, with input,
   output, and cache tokens, and never labeled `actual cost`.
9a. A run whose response carries no usage reads `Cost unavailable`, never $0.
9b. The learned rate moves after a measured run, and the usage history holds
    the underlying record.
10. Caption generation, and drafts persisting immediately.
11. A split run that fails partway keeps every successful group's captions.
12. Deliberate retry sends only the remaining photos.
13. Refresh and restart without losing paid caption work.
14. One-click review of every included caption.
15. Editing a reviewed caption resets its status.
16. Excluded photos do not block Build.
17. Build stays blocked while included captions remain unreviewed.
18. Clear failure with no automatic retry, in plain language, for each of the
    five failure kinds in Section 4a.

**Document**

19. Exact output filename, and collision behavior.
20. Originals proven byte-for-byte unchanged after every build.
21. Temporary optimized copies removed after a successful and a failed build.
22. A directly-placed HEIC builds successfully (currently fails, per Section 1b).
23. DOCX size recorded before and after optimization.
24. Word opens the document on Windows.
25. PDF produced by hand from Word, and its size recorded.
26. Spenser's visual review across landscape, portrait, rotated EXIF, HEIC,
    JPEG, PNG, small, and very large photographs.

**State**

27. Upgrade from one test version to another without losing settings.
28. Rollback to the last working version, launched only after the current one
    is closed.
29. Upgrade survival and rollback survival evidenced **separately** for each of
    the four state files.
30. A malformed settings file produces a clear recoverable error and is not
    mistaken for first-time setup.
30a. The AI Usage History survives upgrade and rollback, and holds no job name,
     address, photo filename, caption, prompt, or key.
30b. Reset Demo restores the hydrated photographs rather than deleting them.
30c. A Local-only demo job is refused before any client is constructed, and the
     refusal survives Reset Demo.
31. The last-known-good record reflects the version that actually ran, and a
    version that dies inside 20 seconds never records itself.

**Evidence discipline**

32. Automated tests, a real screen walkthrough, and a real Windows-machine
    acceptance test remain separate evidence. One never stands in for another.
32a. A hands-on Spenser sandbox session is its own evidence too, and a passing
     suite never stands in for it. See the definition of done in Section 26.
33. Measured file size and visual acceptance remain separate evidence. Size may
    be reported before Spenser's screen review; appearance may not.

**No paid API test, no Windows installation test, no packaging, and no
implementation is performed during this planning checkpoint.**

## 17. Mac regression tests

Everything below runs on the Mac and must be green before any package is sent.

| Test file | Proves |
|---|---|
| existing suite | Nothing regressed. Baseline at branch point: 320 passed, 15 skipped |
| `test_output_naming.py` | The Section 2 parsing cases: commas, unit numbers, missing values, older brief order, stored corrections winning, Windows-forbidden characters, numbered copy on collision, refusal rather than a guess |
| `test_caption_guards.py` | 60 is the ceiling; 61 refuses before any request is attempted; retries are off; the count and the $0.05 arithmetic shown before sending match what would be sent |
| `test_caption_split.py` | Section 3d: failure before any group succeeds, failure after partial success, refresh after partial success, deliberate retry of only remaining photos, and no photo sent twice |
| `test_cost_estimate.py` | Section 3e: the $0.05 prior on the first run, gradual decline after cheaper runs, increase after costlier ones, upward rounding to $0.05, split aggregation, partial success in the denominator, retry linked to its original, missing usage as unavailable, unknown cost never zero, and a new bucket on a model, pricing, or image-settings change |
| `test_usage_history.py` | Section 3f: every field round-trips, a retry carries its parent ID, the stored learned rate reproduces from the record, upgrade and rollback survival tested separately, prior-bucket records retained, and no job name, address, photo filename, caption, prompt, image, or key anywhere in the file |
| `test_caption_errors.py` | Section 4a: each of the five failure kinds produces its own plain sentence, with a stand-in for the model |
| `test_caption_review.py` | Drafts save immediately as unreviewed; a review marks one caption; editing a reviewed caption resets it; excluded photos never block; Build refuses while an included caption is unreviewed |
| `test_package_manifest.py` | Run against output from the committed packaging script: every required path present, every Section 10 exclusion absent, `runtime.json` and the manifest both outside the immutable set, still valid after startup creates and updates `runtime.json`, truncation and missing files and same-size corruption and a moved path all detected, validation before any third-party import, and an identical manifest from identical inputs |
| `test_launcher.py` | Section 5b: bind port 0, record and re-read `runtime.json`, refuse on a live sibling of another version, ignore a stale sibling, never accept a foreign or wrong-version answer, bounded refusal under interference |
| `test_settings_survive_upgrade.py` | Section 5c and 6: four literal filenames, last-good round-trip, no record from a process that dies inside 20 seconds, upgrade and rollback survival tested separately |
| `test_state_atomicity.py` | Section 6: interrupted writes leave the previous file intact for all four files; malformed files produce a clear recoverable error; an unknown schema version is refused |
| `test_photo_optimization.py` | Section 12: originals unchanged by fingerprint, temporary copies removed on success and failure, EXIF orientation applied, longest edge capped at 1,600, quality 85, smaller images never enlarged, HEIC and JPEG and photographic PNG all take the same path |
| `test_ai_policy.py` | Section 25b: Local-only demo photos work locally but never reach the caption client, a renamed or new or unrecognized job defaults to Local only, only an allowlisted job reaches the stand-in client, Reset Demo preserves the restriction, production jobs are unaffected, and no image or address or caption or key is written to the policy file |
| `test_demo_hydration.py` | Task 6: every demo job populated, the read-only source tree fingerprint-identical before and after, Reset Demo restoring rather than deleting the hydration, hydration reproducible, nothing tracked by Git, and every hydrated job Local only until allowlisted |
| `test_file_safety.py` (existing) | Still green. Never weakened |

## 18. Provable on the Mac, versus requires Windows

**Provable on the Mac:** every guardrail's logic, the ceiling and the refusal
at 61, the split and partial-failure behavior, the cost arithmetic, the review
state machine, the filename parsing rules, the non-overwrite behavior, the
port-0 bind and sibling-refusal logic, the failure reporting, the manifest
generation and validation, the atomic-write behavior, the photo optimization
mechanics and the originals-unchanged fingerprint, the wheel availability for
`win_amd64`, and the whole existing suite.

**Requires Windows, and is honestly unproven until then:** that the embedded
runtime starts at all, that the `._pth` configuration honours the packaged
`site-packages`, that the binary wheels import, that `pillow-heif` decodes a
real HEIC there, that the `.bat` double-click works from an Explorer-extracted
folder carrying the Mark of the Web, what SmartScreen actually says, that the
browser opens, that Word opens the output, that `Path.home()` resolves to his
profile, that `bind(0)` yields a usable loopback port, that `runtime.json` is
writable where he unzipped, and that a second version is refused rather than
started.

**Requires a real paid run:** whether the $0.05 estimate is close, and caption
quality on real photographs.

**Requires Spenser's own eyes:** whether the optimized photographs look right
in Word and in the PDF.

No report will say the pilot works on Windows before it has run on Windows.

## 19. Rollback

**DIRECTION, approved 2026-08-18.** The package is versioned and
self-contained, and every piece of Mark's state lives outside it. So rollback
is: keep the previous version's folder, close the current version, and
double-click the previous version's launcher.

Closing first is not optional. Section 5b refuses to start a second version
while one is running, so a rollback attempted without closing produces the
refusal message rather than a silent wrong-version launch.

The last-good record from Section 5c exists so a report can say which version
actually last started. It is evidence for Spenser. Nothing consumes it
automatically, and there is no automatic rollback.

The instruction to Mark is one line in `README FIRST.txt`: keep the previous
folder until the new one has worked once.

There is no automatic updater in this slice, by decision. During the pilot
Spenser installs updates; Mark does not.

## 20. Windows risks

**UNPROVEN, none of these measured:**

- **Antivirus and SmartScreen.** An unsigned `.bat` that launches a bundled
  `python.exe` and opens a listening socket is a recognisable pattern to
  endpoint protection. It may be blocked, quarantined, or delayed. It presents
  in at least three different ways: the "Windows protected your PC" dialog with
  the real button behind "More info"; `python.exe` quarantined so the `.bat`
  reports it cannot find the file; or a delay long enough that the startup
  timeout fires first. **APPROVED, 2026-08-18:** do not purchase or require
  code signing for Mark's pilot. Reconsider it before wider distribution. The
  mitigation is procedural: Spenser is present by screen share, and one
  SmartScreen confirmation is accepted for this pilot only, per Section 14.
- **Firewall prompt, and why it is the least likely of the three.** The server
  binds `127.0.0.1` and never `0.0.0.0` (`run_app.py:13` today, preserved by
  Section 5b). Windows Defender Firewall generally does not prompt for
  loopback-only binds. This is a concrete reason never to change that bind
  address, and it is recorded so a future change does not make it quietly.
- **Permissions.** Unzipping into `Program Files` needs elevation and would
  break the write-nothing-inside-the-package assumption, which Section 5b now
  depends on because `runtime.json` is written there. Mark should unzip into
  his own profile, for example the Desktop or Documents. That belongs in
  `README FIRST.txt`.
- **Local-port and security-software interference.** A corporate proxy or a
  security product may intercept localhost traffic and answer on ports the app
  did not bind. **DIRECTION, approved 2026-08-18:** the failure path is bounded
  and plain. A fixed, small number of probe attempts, then a refusal naming
  what was tried and what answered wrongly. Never an unbounded loop, and never
  treating a foreign answer as success. **TEST:** interference on every probed
  port produces a bounded plain refusal rather than a hang.
- **Path length.** A deep unzip location plus `site-packages` plus long wheel
  paths can approach the legacy 260 character limit on machines where long
  paths are not enabled. Mitigated by unzipping near the top of the profile,
  and checked explicitly by the manifest validation of Section 11.
- **Blocked outbound HTTPS.** Captions need `api.anthropic.com`. Section 4a now
  records what actually happens today: the key-save path degrades well and the
  caption path does not. Fixing the caption path is required, not optional.

## 21. The smallest technical spike

**DIRECTION, approved 2026-08-18.** One spike, on Windows, before any pilot
feature work:

Assemble a package with the committed packaging script of Section 11,
containing the embedded runtime, the installed wheels, the built interface, and
today's unmodified app plus the `VERSION` file, the `/api/version` endpoint, the
port-0 bind, and the manifest check. Deliver it through the Section 14 path.
Unzip it on Windows with Explorer. Double-click. Confirm the browser opens the
working app on the bound port, that the version shown matches the folder, that
the state files appear in Mark's profile, and that stopping and restarting
works. Then unzip a second version beside it and launch it.

**The success criterion for the second copy, corrected.** The previous revision
said "confirm both run and share the same settings". That was scoring a
corruption test as a pass, given `busy.py:31`. The criterion is now:

> The second launch is **refused**, and the displayed version matches the
> folder launched.

**What that spike would settle:** the embedded runtime, the `._pth` behavior,
the binary wheels including `pillow-heif`, the launcher, the manifest check,
the browser open, `Path.home()`, `bind(0)`, `runtime.json` writability, the
real SmartScreen prompts, and the versioned-folder rollback premise with its
single-instance guard. Most of the largest unknowns, with no pilot feature code
written and no paid API call.

**What it would not settle:** captions, cost, split-run failure, filenames,
review state, photo optimization appearance, or anything about Office.

## 22. Alternatives and tradeoffs

Where the technical direction is now approved, the rejected option is recorded
with it, so a later session does not relitigate it and does not mistake the
decision for an accident.

| Question | Chosen | Rejected, and why |
|---|---|---|
| Runtime | Embeddable zip | A frozen single-file binary is less work to hand over and is rejected because a pilot exists to produce diagnosable failures. When the embeddable fails, `python.exe` is a real interpreter Spenser can run by hand over screen share. A full installer is rejected as more machinery than six versions need |
| Runtime version | **CPython 3.14**, approved 2026-08-19 on Task 1 evidence | 3.9 through 3.12 are rejected because python.org stopped publishing their Windows embeddables, leaving 12, 10, 7, and 4 security releases with no binary. 3.13 is rejected because its bugfix window closes around October 2026 and its embeddable then freezes the same way. Not chosen for being newest |
| Launcher | `.bat` shim with the logic in Python, console visible | `.vbs` to hide the console is rejected because it makes failure invisible. A signed `.exe` shim is out per the approved no-signing decision |
| Launcher liveness probe | `GET /api/version` | `/api/demo` is rejected because Section 10 removes it from the package, so the probe would work on the Mac and fail on Mark's machine |
| Port | Bind `0`, record in the version's `runtime.json` | Fixed 8000 is rejected because it makes two versions indistinguishable. Walk-up from 8000 is rejected because it starts a second copy, which `busy.py:31` does not guard, and because it has no terminating condition under localhost interference |
| Two versions at once | Refused, with the running version named | Allowing both is rejected: nothing guards two processes writing the same state files |
| Version display | `VERSION` file plus `/api/version` | A source constant is rejected because packaging writes the file, rollback distinguishes it, and the endpoint is also the launcher's probe and the last-good check. Display was never the only purpose |
| Last-good record | Its own `~/.rrf-app-version.json` | Inside `~/.rrf-app.json` is rejected: that file is written most often, written non-atomically, and fails silently, so the crash-recovery record would be lost by exactly the events it exists to survive |
| Rollback | Manual, after closing the running version | Automatic rollback is rejected: a false positive would produce a failure Mark cannot describe, and Spenser is present during the pilot |
| Integrity | Immutable manifest of ordered paths and sizes plus one aggregate over paths, sizes, and contents, checked by the launcher. `runtime.json` and the manifest itself sit outside the set | A checksum Mark compares by hand is rejected as a second step on his machine. Per-file hashing is rejected as slow across thousands of `site-packages` files for no protection that matters here. Including `runtime.json` is rejected because the app would invalidate its own package on first startup |
| Update delivery | Full package each time | A diff or patch is rejected: it is smaller but introduces exactly the interrupted-update failure mode the manifest check exists to catch |
| Delivery path | Private download link | A shared folder or USB is rejected as a *test* path because it avoids the Mark of the Web and would pass while the real path fails |
| Photo size in the document | Temporary optimized copies at 1,600 px, quality 85 | Recompressing the originals is rejected outright and is forbidden by the Never list. Relying on the existing AI thumbnail is rejected because it never reaches the document. Leaving it alone is rejected because a 60-photo report of phone photographs produces a file Word and email both struggle with |
| Cost estimate | Adaptive rate from a heavy $3.00-over-60 prior, rounded up, labeled a maximum | A fixed $0.05 forever is rejected because the first real run makes it measurably wrong. Using only the last observed rate is rejected because one cheap run would swing the number Mark reads before spending money |
| Post-run cost wording | `Calculated API cost from measured usage`, with tokens shown | `Actual cost` is rejected: it is this app's arithmetic over a price table, not a bill. The billing console stays the invoice authority |
| Cross-process safety | Single-instance refusal | A lock file is rejected: it adds a stale-lock failure mode worse than what it prevents |

**Not chosen on convenience.** Where the easier option was the worse one it is
named as rejected above, with the reason. The embeddable runtime, the full
package, the single-instance refusal, and the manifest check are all more work
than their alternatives.

## 23. Exact stop conditions

Stop and report, without proceeding, when any of these is true:

1. `test_file_safety.py` fails, or any test shows a source file changed.
2. Any original photograph is changed, renamed, moved, or deleted by any code
   path, or a fingerprint comparison cannot prove it was not.
3. A wheel has no `win_amd64` build, so the package cannot be assembled.
4. **HEIC support fails.** Return evidence. Do not silently remove HEIC
   support and do not silently change runtime versions.
4a. **The packaged runtime cannot import `anthropic` and its complete
    dependency chain on Windows.** Do not continue. Do not work around it by
    trimming the closure, and do not silently change the runtime. Section 7c
    records why this stop condition exists: a hand-written dependency list
    already dropped `httpx` once.
4b. **A Local-only demo job could reach the caption client**, or the Section 25
    policy cannot be shown to refuse before a client is constructed.
5. The suite is not green at the end of any task.
6. A packaging step would include anything in the Section 10 exclusion list.
7. The confirmed city or address is unavailable and the code would have to
   infer either one.
8. A run would send more than 60 photos, or would send anything before the
   count and the cost estimate have been shown, or would re-send a photo that
   already carries a caption.
9. Any acceptance item in Section 16 fails.
10. Two versions could run at once, or a launcher could accept another
    version's response as success.
11. Any choice appears that materially affects Mark's setup, AI spending,
    privacy, file safety, delivery, permissions, or scope and is not already
    approved here.
12. The work would touch Description of Improvements beyond the single disabled
    row named in Section 13.

## 24. Decisions still needed

**From Spenser: none outstanding. No OPEN item remains anywhere in this
document.** Every product question raised on 2026-08-17 was answered on
2026-08-18. Every technical question the independent review raised on
2026-08-18 was answered the same day. The two OPEN items that survived that
revision were both closed on 2026-08-19: post-run cost wording in Section 3e,
and caption-versus-key failure messages in Section 4a. Recorded so nobody
reopens them:

- The estimate starts at $0.05 per included photo and learns from measured
  usage, rounded up, labeled `Estimated maximum cost` (Section 3e).
- Post-run wording is `Calculated API cost from measured usage`, never
  `actual cost`. The billing console is the invoice authority.
- The app keeps a local AI Usage History holding counts, tokens, and rates, and
  no job or client content (Section 3f).
- The provider limit is $20 with notifications to Spenser.
- `Planned workflows` shows Description of Improvements alone.
- Version identity is a `VERSION` file plus `GET /api/version`.
- The launcher binds port 0, records it, and refuses a second version.
- Last-known-good lives in `~/.rrf-app-version.json`, at 20 seconds, recorded
  by the server, with no automatic rollback.
- Packaging is a committed script with an immutable manifest and an aggregate
  over ordered paths, sizes, and contents. `runtime.json` and the manifest sit
  outside that set.
- Delivery is a private download link, with one SmartScreen confirmation
  accepted for this pilot only.
- A split run keeps paid work and retries only what remains.
- Report photos are optimized as temporary copies at 1,600 px quality 85, and
  originals are never touched.
- Code signing is out for the pilot and revisited before wider distribution.
  The integrity check catches damage, not an adversary, and Section 11 says so.
- The live HEIC defect is fixed inside Task 4, with no separate Mac hotfix,
  while HEIC dependency viability is still proven first in Task 1.
- The pilot runtime direction is CPython 3.14, on the Task 1 evidence in
  Section 7b, and real imports stay unproven until Gate A.
- `httpx` and its chain ship. The packaging script derives the closure rather
  than keeping a hand-written list (Section 7c).
- Demo material is hydrated into the demo baseline so Reset Demo restores it,
  as Task 6 of Section 26.
- Demo material defaults to Local only, and an app-owned policy blocks it from
  external AI in code unless explicitly marked AI safe (Section 25).
- Done means the eight-item definition at the head of Section 26, not working
  code and not a green suite.
- The work runs as the eight tasks and four approval gates of Section 26.

**Discovered during this revision, and needing Spenser only if the evidence
comes back badly:**

- **If `pillow-heif==1.1.1` has no compatible Windows wheel**, Section 7 stops
  and returns evidence. Whether to change the runtime version, change the pin,
  or change HEIC support is a product decision and none of them may be taken
  by the executor.
- **If Spenser's screen review finds the optimized photographs unacceptable**,
  the 1,600 px and quality 85 figures are the dials, and changing them is his
  call.

**Not authorization.** Approval of this plan's product decisions and technical
direction is not approval to implement. Implementation waits on Spenser's
explicit yes to begin Task 1 of Section 26, and then stops at Gate A.

## 25. Demo material, corpus classes, and the AI policy

**APPROVED, 2026-08-19.** Demo photographs make the workflow testable. They
also create a way for real property imagery to reach an external service by
accident. This section is how both are handled, and the second half of it is
code, not a naming convention.

### 25a. The two corpus classes

| Class | May contain | Used for | May reach Anthropic |
|---|---|---|---|
| **Local layout corpus** | Images copied or extracted from sample reports | Local screens, document building, Word and PDF size, orientation, visual review | **No.** Never, without a later explicit approval from Spenser |
| **AI-safe stress corpus** | Generated images, or photographs Spenser explicitly approves for external AI use | Paid caption testing, cost learning, split runs, retries, caption-quality review | Yes, and only these |

**Why the local class exists at all.** Sample-report photographs are real
property imagery belonging to Mark's clients. Coming from an example report
does not make them sendable. They are useful for everything that happens on
this machine, and for nothing that leaves it.

**FACT, and the reason naming is not enough.** The caption route sends whatever
`photos_routes.included(manifest)` yields for a job, confined to that job's
`Photos` folder (`main.py:386-394`). Nothing in that path consults a folder
name, a filename, or a fixture label. A convention that lives only in names
would be enforced by whoever remembers it.

### 25b. The app-owned AI policy

**APPROVED, 2026-08-19. Naming and folders alone are insufficient enforcement.**
The policy is app-owned state stored outside all job folders, alongside the
other app-owned files of Section 6 and written with the same atomic helper.

- **The demo root is derived, never registered by hand.** It comes from the
  existing validated `.rrf-demo.json`, through the same validation
  `demo.enabled()` already performs. The policy trusts the root only when that
  validation succeeds, and the working root must resolve to the exact approved
  `RRF Demo Jobs` location `demo.py` already enforces (`demo.py:35-40`,
  `demo.py:150-163`).
- **No user, Builder, test helper, or application screen can type a different
  demo root and have it treated as trusted.** There is no manual root-entry
  function to call.
- **If demo validation fails, no job becomes AI safe.**
- **A demo copy outside the validated demo root is not automatically trusted
  or AI safe.**
- **The entire validated demo root defaults to `Local only`.** Default-deny,
  not default-allow.
- It maintains an **explicit allowlist of demo jobs marked `AI safe`**.
- **A renamed, moved, newly added, or unrecognized job under that demo root
  stays Local only.** Falling off the allowlist can only ever make a job more
  restricted, never less.
- **Reset Demo does not erase or weaken the policy.**
- **The caption endpoint checks the policy before constructing an API client
  or sending any image.**
- A Local-only demo job gets a plain refusal saying its photographs are
  restricted to local testing.
- **The refusal happens before any external request, any token usage, and any
  cost.** Same shape as the 61-photo ceiling in Section 15, and provable the
  same way at zero cost.
- **Production jobs outside the validated demo root are not silently
  reclassified by this demo-only policy.** It restricts demo material; it does
  not quietly change how Mark's real jobs behave.
- **No Mark-facing control for changing this policy ships in the pilot.** There
  is no switch on a screen.
- **AI-safe status is established only through the controlled demo-preparation
  workflow**, after Spenser approves the corpus.
- **Naming alone never grants AI permission.** Not a folder name, not a
  filename, not a fixture label.

### 25c. Which task owns which half

**APPROVED, 2026-08-19.** The policy is built in one task and connected in
another, so neither can be assumed done because the other is.

| Task | Owns |
|---|---|
| **Task 2** | Safe AI-policy storage, validated demo-root derivation, default-deny evaluation, and their tests. No caption-route wiring |
| **Task 4** | Connecting that policy to the caption endpoint, and proving refusal happens before an Anthropic client is constructed |
| **Task 6** | Hydrating the demo baseline and establishing the explicitly approved AI-safe allowlist |

Task 2 leaves an explicit code and test boundary showing that Task 4 must call
the evaluation before constructing the client. Until Task 4 lands, the policy
exists and is correct and nothing consults it, and no report may describe the
caption route as guarded.

**What the policy file may hold:** the resolved demo root, the allowlist of job
names under it, and a schema version. **What it may never hold:** a source
image, an address, a caption, or an API key. Job names under the demo root are
the allowlist's only possible key, so they are recorded; nothing else about a
job is.

**TEST, required before acceptance.** In `test_ai_policy.py`, with a stand-in
for the model so cost is zero:

- Local-only demo photographs can be viewed, reviewed, optimized, and built
  locally. The restriction blocks sending, not working.
- **Local-only photographs cannot reach the caption client**, asserted by
  proving no client was constructed and no request attempted.
- A renamed job inside the demo root defaults to Local only.
- A newly added job inside the demo root defaults to Local only.
- An unrecognized job inside the demo root defaults to Local only.
- **Only an explicitly allowlisted AI-safe demo job reaches the stand-in
  caption client.**
- Reset Demo preserves the effective restriction.
- A production job outside the demo root is unaffected by the policy.
- A valid demo configuration derives the exact approved working root.
- No manual root can be substituted for the derived one.
- An invalid demo configuration yields Local only and never AI safe.
- **No source image, address, job name outside the demo root, caption, or API
  key is written into the policy file**, asserted by scanning the written
  file's bytes.

## 26. The execution plan

**APPROVED, 2026-08-19.** Everything above this section is requirements. This
section is the order the work is done in, the gates it stops at, and what each
stop must produce. Without it the document says what to build and never says
when to stop.

**Nothing here is authorization to start.** Each task begins only on Spenser's
explicit yes.

### Definition of done

**APPROVED, 2026-08-19.** The Windows Photo Pilot is done only when all eight
of these hold:

1. Every approved behavior is implemented and tested.
2. Spenser completes at least one hands-on sandbox session using the complete
   feature.
3. Problems from that session are captured.
4. Any required usability facelift is completed as a separate bounded
   refinement.
5. Visible refinements receive another screen review.
6. The exact candidate package passes Windows installation, startup, Word and
   PDF, update, rollback, SmartScreen, and recovery testing.
7. Spenser approves that exact package.
8. The approved package and private download link are ready for Spenser to
   install with Mark over screen share.

**Working code does not independently meet this. Nor does a green suite. Nor
does an existing zip.** Each of those is necessary and none of them is
sufficient, and a report that offers one of them as completion is wrong.

### Rules that bind every task

Every task, without exception:

- Begins from a verified clean working tree on this branch.
- Names the exact files it may change, before it changes any of them.
- Runs its own focused tests **and** the full suite: `python3 -m pytest app/tests -q`
- Includes a real screen review when visible behavior changes.
- Commits only its bounded scope.
- Returns the four-part Product Control Brief of `HOW-WE-WORK.md`.
- Stops at every approval gate.
- Never pushes, merges, delivers, or treats work as accepted without explicit
  authorization.

### Task 1: Prove Windows dependency viability. COMPLETE 2026-08-19

Outcome recorded as FACT in Section 7a. Every pinned dependency resolves to
binary `win_amd64` wheels on all six candidates, HEIC stays in scope, and the
runtime direction of Section 7b follows from it. Task 1 changed no repository
file. What it did not prove is in Section 7a's UNPROVEN list.

The original scope, kept for the record:

- Check the targeted `win_amd64` wheels, `pillow-heif==1.1.1` first and alone
  so its answer is unambiguous.
- Decide the runtime version **from that evidence, not from preference**.
- Make no product compromise if HEIC fails.
- **Stop and report if any required wheel or import path is unproven.**

Files this task may change: none in `app/`. It produced evidence, not code.

### Task 2.1: Make the damaged-state message reach the screen. COMPLETE 2026-08-19

**FACT, 2026-08-19.** Task 2 made the API tell the truth and the screen threw
it away. `App.jsx` caught the failure with `.catch(() => ...)`, which discards
the error, and substituted "Could not reach the app's server. Close this tab
and start the app again." For a damaged settings file that was wrong twice: it
named the wrong cause, and it sent Mark round a restart loop that cannot fix a
file on disk.

What changed:

- The damaged-state response carries a `state_unreadable` flag as well as the
  approved sentence, so the screen identifies the case rather than matching
  text. 409 alone was not enough, because `busy.Busy` answers 409 too.
- `api.js` attaches the status and that flag to the Error it already threw.
  Its message is unchanged, so every existing caller keeps the sentence it
  showed before.
- `App.jsx` shows the server's sentence for that one flagged case, and the
  existing connection message for everything else, including a fetch that
  never got an answer.
- The approved sentence is not copied into JavaScript. It lives in
  `state.RECOVERABLE_MESSAGE` and is displayed from the response, so there is
  no second copy to drift.

**No automatic repair behaviour was added.** Task 2.1 explains the problem. It
does not rename, delete, rewrite, or repair the file, and no route or control
was added that would. Verified by eye on the real app against a deliberately
malformed file in an isolated state folder: the sentence rendered, the file was
unchanged afterwards, and no path, traceback, or parser text appeared.

**Writer-version history was explicitly deferred**, 2026-08-19. Recording which
version wrote each state file would let a rollback warn that a newer version's
settings are being read by an older one. Spenser judged that unnecessary
complexity for this pilot. **Schema versions remain the rollback protection**,
and an unknown future schema is refused rather than truncated, which is the
half that actually prevents data loss.

**Task 3 remains unauthorized.**

### Task 2: Make app-owned state safe

- The shared atomic-write helper of Section 6.
- Clear malformed-state recovery, replacing the silent empty-dict behavior.
- Schema versions on structured JSON state.
- The separate last-known-good file, `~/.rrf-app-version.json`.
- The local AI Usage History storage structure of Section 3f.
- Automated state, privacy, interruption, upgrade, and rollback tests. Upgrade
  and rollback proven **separately**, never as one case.

### Task 3: Build the Windows delivery spine

- The reproducible packaging script of Section 11.
- `VERSION` and `GET /api/version`.
- The dynamic loopback port.
- `runtime.json`, created after validation, outside the immutable set.
- Single-instance refusal.
- Immutable manifest validation.
- Plain startup failures.
- A self-contained Windows package.

**Built and Mac-tested 2026-08-19. Two defects found by running it, both
fixed:**

- **The manifest check refused to start in the development checkout**, which
  has no MANIFEST and never will. It now skips there, decided by the presence
  of `app/tests`, which is on the exclusion list and can never be in a
  package. Deciding it by the absence of the manifest would have been wrong:
  that is exactly what a half-finished unzip looks like, so it must stay an
  error in anything shaped like a package.
- **`main.py` imported `demo` unconditionally**, so excluding `demo.py` from
  the package stopped the whole server importing and the app did not start at
  all. Section 10a predicted this in words and nothing proved it until a
  package was built and run. The import, the exception handler and both routes
  are now conditional, and a test runs the packaged `main.py` to prove it.

**FACT, measured on the Mac 2026-08-19.** The package builds and verifies
itself: 2,472 files, embedded CPython 3.14.7, the full 33-distribution runtime
closure resolved for `win_amd64` including `httpx`, with `uvloop` correctly
absent and `demo.py` absent. A missing file, a truncated file, a same-size byte
corruption and a moved file are each detected, and the missing one is named.
Two package folders side by side refuse to run at once and name the running
version; closing one and launching the other shows the version whose folder was
launched.

**Still unproven, and the reason Gate A exists.** None of it has run on
Windows.

**Task 3.1, 2026-08-19: the downloadable archive.** Task 3 produced a package
folder. The approved delivery path in Section 14 is a private download link,
and you cannot link to a folder, so the ZIP was missing.

ZIP creation, the external SHA-256 sidecar, and a fresh-extraction check are
now part of the same committed packaging script. One command produces the
folder, `Roy R. Fisher v0.1.0.zip`, and `Roy R. Fisher v0.1.0.zip.sha256`.

**The exact archive is identified by its external SHA-256.** That is how
Spenser approves one build rather than a build, per Gate D. **Mark never
compares a checksum**: the launcher checks the package's own MANIFEST after he
unzips, and he is asked for nothing.

**Two things found while making it reproducible, both fixed.**

- **pip was writing the build machine's absolute paths into every installed
  `RECORD`**, through byte-compilation into a randomly named temporary
  directory. Spenser's username shipped inside the package, and the random
  segment changed the bytes on every build, so the archive could never have had
  a stable hash. Byte-compilation is now off, which is right anyway: a `.pyc`
  built by this Mac's Python 3.9 is useless to a Windows 3.14 interpreter.
- **`direct_url.json` recorded a `file:///Users/...` URL for every
  distribution.** Optional metadata nothing reads at runtime, deleted after
  install. It would also have made two different machines produce different
  archives forever.

**FACT, measured 2026-08-19.** Two full builds from the same cached inputs
produce byte-identical archives. 34 MB, 2,440 entries, one top-level folder,
no links, no path escaping it, no `runtime.json`, no build-machine paths.
Fresh extraction validates against the package's own MANIFEST.

**Mac extraction and manifest verification do not satisfy Gate A.** Python's
`zipfile` on a Mac says nothing about Windows. **Gate A still requires the
archive downloaded through a browser, extracted by Windows Explorer,
SmartScreen observed and its exact wording recorded, and the app actually run
on Windows.** Task 4 remains unauthorized.

### Approval Gate A: Windows spine proof

**Stop after the smallest Windows spike of Section 21.** Report what actually
ran on Windows:

- The SmartScreen experience, prompts recorded word for word.
- Dependency imports.
- Version identity, and that the version shown matches the folder launched.
- State paths, and where `Path.home()` actually resolved.
- Startup and shutdown.
- Second-copy refusal.
- The rollback premise.

**Do not begin Photo Pilot feature implementation until Spenser approves
continuing.**

### Task 4: Implement the Photo Pilot backend

- Output naming, and the confirmed city and address, parsed per Section 2.
- The 60-photo ceiling.
- Split requests and partial-failure preservation.
- The adaptive pre-run estimate of Section 3e.
- Measured usage capture and the local run history of Section 3f.
- Unreviewed drafts and per-photo review state.
- HEIC-safe temporary document copies. **This is where the Section 1b defect is
  fixed.**
- Photo optimization per Section 12.
- Original-file fingerprints and safety tests.

### Task 5: Implement the Photo Pilot frontend

- `Estimated maximum cost` before sending, with its arithmetic.
- `Calculated API cost from measured usage` and token usage afterward.
- The partial-run and retry experience.
- One-click `Reviewed` controls and visible progress.
- Build gating.
- Version display on every screen.
- The `Planned workflows` band containing only Description of Improvements.
- Clear errors, and no inactive controls that look clickable.

### Task 6: Demo Hydration

**APPROVED, 2026-08-19.** Runs after the frontend and **before Gate B**,
because Gate B is a hands-on session and an empty demo job cannot be used
hands-on.

- Populate the `Photos` folder in **every** demo job.
- Work only in disposable, app-owned demo copies.
- Keep all hydrated material out of Git.
- **Never modify source reports, evidence, original client folders, or original
  photographs.**
- **Hydrate `.rrf-demo-baseline/RRF Demo Jobs`, then use the existing Reset
  Demo flow to create or restore the working `RRF Demo Jobs`.**
- **Prove Reset Demo restores the hydration instead of deleting it.**
- Fingerprint the source material before and after extraction or copying.
- **Prove the read-only source tree remains unchanged.**
- Make hydration **reproducible**, not dependent on undocumented manual
  copying.

**Why hydration targets the baseline and not the working folder. FACT:**
`demo.py` replaces the whole working folder with the baseline, and its own
docstring says anything not in the baseline is simply gone. The approved paths
are baseline `.rrf-demo-baseline/RRF Demo Jobs` and working `RRF Demo Jobs`
(`demo.py:35-40`). Hydrating the working folder directly would be erased by the
first Reset Demo. Hydrating the baseline makes Reset Demo restore the
photographs instead, which is what Spenser approved on 2026-08-19.

**FACT, so nobody builds machinery for it.** Keeping hydrated material out of
Git is already free. `.gitignore` carries `**/Photos*/**` with a
`!**/Photos*/GUIDE.md` re-include, and `RRF Demo Jobs/` and
`.rrf-demo-baseline/` are ignored outright. Photographs placed in these folders
are ignored more than once.

**Scenarios distributed purposefully across the demo jobs**, so each one
exercises something different rather than every job looking the same:

| Scenario | Purpose |
|---|---|
| Normal 12-photo job | The ordinary path, and the $0.05 arithmetic example |
| 60-photo maximum | The ceiling exactly at its limit, and a real split run |
| 61-photo refusal | The refusal, provable at zero cost per Section 15 |
| Large phone photographs | Section 12 optimization, and DOCX size before and after |
| HEIC | The live Section 1b defect, placed directly and not uploaded |
| JPEG | The common case |
| PNG | The photographic-PNG path of Section 12 |
| Portrait and landscape | Layout in the built document |
| Rotated EXIF | Orientation applied before resize, which is new behavior |
| Small images that must not be enlarged | The never-enlarge rule |
| Excluded photographs | That exclusions never block Build |
| Draft, reviewed, and edited-caption fixture states | The review state machine, where fixtures are appropriate |

**Every demo job must have enough photographs to make the workflow feel real.**
A job with three photographs does not tell Spenser what sixty feels like.

**Corpus classification is not optional here.** Everything hydrated from sample
reports is **Local layout corpus** under Section 25 and is Local only by
default. Nothing becomes AI-safe by being hydrated.

**TEST, required before acceptance.** In `test_demo_hydration.py`:

- Every demo job has a populated `Photos` folder after hydration.
- A fingerprint of the read-only source tree is identical before and after.
- No source report, evidence file, client folder, or original photograph is
  modified, renamed, moved, or deleted.
- **Reset Demo restores the hydrated photographs rather than removing them.**
- Hydration is reproducible: running it twice yields the same baseline.
- Nothing hydrated is tracked by Git.
- Every hydrated job is Local only under the Section 25 policy until
  explicitly allowlisted.

### Approval Gate B: Spenser's hands-on sandbox session

**APPROVED, 2026-08-19. Stop after automated tests and a real hands-on session
using the hydrated demo jobs of Task 6.** This is not a walkthrough of a script.
It is Spenser freely using and experimenting with the feature, which is why
Demo Hydration comes first.

**Spenser must be able to:**

- Generate or enter captions
- Edit captions
- Click each `Reviewed` control
- Exclude and restore photographs
- Observe review progress
- Attempt Build before and after review completion
- Inspect output naming
- Open the optimized Word document
- Save or inspect the PDF
- Compare file size and image quality
- See the `Planned workflows` presentation
- Refresh and restart to confirm state survives

**If the session finds usability problems:**

- Capture them.
- Propose **one bounded refinement task**.
- **Wait for approval before implementing any new product behavior.**
- Repeat the screen review when visible behavior changes.

A refinement is a separate bounded task, not a set of fixes folded quietly into
whatever comes next. It is item 4 of the definition of done above.

**Do not proceed to paid AI calibration until Gate B is explicitly accepted.**
Do not create Mark's delivery package before that either.

### Task 7: Bounded paid AI calibration

**APPROVED, 2026-08-19.** Uses **only the AI-safe stress corpus of Section 25,
explicitly approved by Spenser.** The Local layout corpus never takes part, and
Section 25b's policy makes that a refusal in code rather than a promise.

Coverage required:

- A normal run.
- A split run.
- Partial success.
- Manual retry of **only the remaining photographs**.
- **Proof of no duplicate charging.**
- The adaptive estimate, verified moving as Section 3e says it should.
- Local usage-history accuracy, verified against Section 3f.
- Caption quality, reviewed on real photographs.
- **Remaining within the $20 provider limit.**

Record measured usage, calculated cost, the learned-rate change, caption
quality, and any failed request.

**Do not use client photographs without explicit corpus approval.**

### Approval Gate C: Cost and caption acceptance

**Stop and report the calibration evidence.** Spenser decides whether the
estimate, the model, and the caption quality are acceptable.

**If the stress test reveals a usability problem, propose a bounded refinement
and wait for approval. Do not proceed directly to the final Windows package.**

### Task 8: Windows package acceptance

- Build the exact candidate package through the committed script.
- Deliver through the approved private-download path of Section 14.
- Test browser download, Explorer extraction, SmartScreen, startup, Word
  output, PDF size, state survival, upgrade, rollback, and failure recovery.
- Use the full acceptance checklist of Section 16.
- **Record the exact package version and the immutable package aggregate.**

### Approval Gate D: Exact package approval

**Stop before sending anything to Mark.**

Spenser approves or rejects **the exact tested package**. Approval of an
earlier build, an earlier plan, or an earlier test does not authorize a
different package. A rebuild is a new package and needs its own yes.

### The gates at a glance

| After | Gate | What it protects |
|---|---|---|
| Task 3 | A: Windows spine proof | No feature work is built on an unproven Windows foundation |
| Task 6 | B: Spenser's hands-on sandbox session | No money is spent, and no package is cut, before the experience is right. Demo Hydration comes first because the session needs real photographs to use |
| Task 7 | C: Cost and caption acceptance | The estimate and the caption quality are judged on evidence |
| Task 8 | D: Exact package approval | Mark receives only a package Spenser tested and named |

**The eight tasks in order:** dependency viability (complete), safe app-owned
state, Windows delivery spine, Photo Pilot backend, Photo Pilot frontend, Demo
Hydration, bounded paid AI calibration, Windows package acceptance.

## Appendix: what this revision changed and why

Recorded so the difference between the previous revision and this one is
legible without a diff.

| Change | Reason |
|---|---|
| Five labels instead of four, adding DIRECTION and UNPROVEN | Technical direction is now approved, and approved must not read as proven or built |
| `/api/version` replaces `/api/demo` as the launcher probe | The old probe could not work in the shipped package, because Section 10 removes the demo routes |
| Conditional import and exception-handler handling for `demo.py` | Deleting the file alone stops the server importing at all (`main.py:14,98`) |
| Bind port 0, `runtime.json`, sibling scan, single-instance refusal | A version-blind probe served the wrong version on both upgrade and rollback; the walk-up alternative started an unguarded second process |
| Last-known-good moved to its own file, threshold set at version match plus 20 seconds, written by the server | The old location was the file most likely to be damaged by the events the record exists to survive |
| New Section 6 on safe app-owned state | Only one of the three state files was written atomically, and an unreadable file was silently indistinguishable from first-time setup |
| New Section 11 on reproducible packaging and integrity | There was no packaging tooling, and the manifest test had nothing producing the tree it asserted against |
| The 3.12 wheel-coverage claim withdrawn | It was asserted where it should have been measured |
| New Section 12 on report photo optimization | The builder embeds original bytes; the existing thumbnails never reach the document |
| New Section 1b on the HEIC build defect | Found during verification. A directly-placed HEIC fails Build today |
| New Section 3d on split-run partial failure | The 60 ceiling and the one-request rule cannot both hold, and the old plan did not say what happens to paid work |
| New Section 4a on differing network failures | Key-save degrades well and captions do not. This closes an OPEN question with evidence |
| New Section 14 on delivery | The Mark of the Web is a technical difference between delivery paths, not logistics |
| Output naming reframed as parsing | Recovering two values from one joined string can be wrong, and the old wording read like a field read |
| The two-copy spike criterion inverted | It scored a corruption test as a pass |
| Section 22 records rejected options with reasons | So the decisions are not relitigated and are not mistaken for accidents |

**Corrections of 2026-08-19.**

| Change | Reason |
|---|---|
| Sections 3e and 3f: adaptive cost estimate and local AI Usage History | A fixed $0.05 is measurably wrong after the first real run. The heavy prior stops one cheap run from swinging the number, and the history makes the rate auditable rather than trusted |
| Post-run wording fixed to `Calculated API cost from measured usage` | `Actual cost` claims a bill the app cannot produce. This closed the last OPEN item, which had been delegated to the executor |
| `Cost unavailable`, never $0, and unknown costs never lower the rate | A missing number is not a cheap number, and treating it as one would bias the estimate downward exactly when evidence is weakest |
| Usage history privacy boundary written as a requirement with a byte-scan test | A cost audit needs counts, tokens, and rates. It does not need to know what the photographs were of |
| `runtime.json` removed from the packaged tree, created after validation, outside the immutable set | The previous revision would have had the app invalidate its own package on first startup |
| The manifest excluded from its own aggregate, and the aggregate defined over ordered paths, sizes, and contents | A file cannot hash itself, and the previous wording never said how the aggregate was computed |
| Section 11 now states plainly what the check does not do | Without code signing it detects damage, not an adversary who rewrites files and manifest together. Saying so is better than implying otherwise |
| An execution plan added, seven tasks and four approval gates at the time | The document was all requirements and no sequence, so nothing said where to stop. It became Section 26 with eight tasks at the 2026-08-19 checkpoint below |
| HEIC sequencing recorded in Section 1b | The defect is live on the Mac, so when it gets fixed had to be a decision rather than a drift |

**Checkpoint of 2026-08-19, after Task 1.**

| Change | Reason |
|---|---|
| Section 7 rewritten around the Task 1 evidence, as FACT with provenance | The runtime question was answered by measurement, so the section that framed it as open had to stop saying so |
| CPython 3.14 recorded as the approved runtime direction | python.org stops publishing Windows embeddables at the bugfix boundary, leaving 3.9 through 3.12 missing 12, 10, 7, and 4 security releases, and 3.13 two months from the same cliff |
| Section 7c: `httpx` is not test-only | `anthropic==0.121.0` requires it unconditionally. The old wording would have produced a package that fails only on Mark's machine |
| The compiled set corrected from three packages to nine | `lxml` and `jiter` were never listed, and four uvicorn extras were treated as incidental |
| The packaging script must derive the closure from resolved metadata | A hand-written list already lost `httpx` once, and a second hand-written list fails the same way somewhere new |
| Stop condition 4a added | If the packaged runtime cannot import `anthropic` and its chain on Windows, trimming the closure is not the fix |
| Section 25: two corpus classes and an app-owned AI policy | Sample-report photographs are real client imagery. The caption route consults no filename, so a naming convention would be enforced only by memory |
| Definition of done, eight items, opening Section 26 | Working code, a green suite, and an existing zip were all being treated as if any one of them meant finished |
| Task 6 Demo Hydration inserted, later tasks renumbered to eight | Gate B is a hands-on session and an empty demo job cannot be used hands-on |
| Hydration targets the demo baseline, not the working folder | `demo.py` replaces the working folder wholesale, so hydrating it directly would be erased by the first Reset Demo |
| Gate B moved after Task 6 and expanded into a real sandbox session | It had been placed before the task that makes it possible |

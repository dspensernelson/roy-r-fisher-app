# Plan: five fixes for the photo screen

## Context

Mark's assistant opens Subject Photographs on her Windows PC and the screen
sits on `Loading...`. It has sat for 20 minutes. Nobody can say whether it is
slow or dead, because the app writes nothing down. She is also afraid of
losing the captions the model wrote, because there is no spare copy of the file
that holds them.

Measured on 2026-09-02, on the Blaul Lofts test job, on Spenser's Mac:

- One click of `Mark Reviewed` opens **130 photograph files**. 51 ms here.
  Her machine reads those over a mapped network drive, `Z:`.
- Opening the photo screen costs the same 130. So does cutting a photograph.
- The cause: `load_manifest` reads each photograph's capture date to order new
  entries, and never saves what it read. `sorted()` calls its key function once
  per item, so it is one open per file, not more. That was checked.
- Two reads per screen open, not one: `GET /manifest` and
  `GET /caption-estimate` both call `load_manifest`, and the second is gated on
  the first, so they run back to back.

A second, separate defect was proven the same day: the photo screen sticks
forever on the top of the Photos folder, because the chosen folder is stored as
`""` and the screen tests it for emptiness rather than absence. She never
reaches it, because the screen stops at `Loading...` above it.

**Approved by Spenser on 2026-09-02**: five slices in the order below, the
spare copy of the captions kept hidden in the app's own folder, and 0.6.1
delivered through the update button, which he will test on his own Windows
virtual machine first.

## Rules for whoever executes this

Read `HOW-WE-WORK.md` and `docs/ROADMAP.md` first. They govern. In particular:

- **One branch per slice.** Commits on it are recovery checkpoints and are
  allowed, because this plan is approved. **Nothing is pushed, merged, or
  delivered without Spenser saying yes.**
- **Never write into `Report Examples/`. Never move, print or log a key.**
- **No em dashes.** Anywhere. Hyphens instead.
- **Python 3.9 compatible.** No `int | None`, no `match`.
- **Test first.** Write the failing test, watch it fail, then fix it.
- **Do not create any markdown file, doc or note this plan does not name.**
- Commit style, matching the last thirty commits: a `feat:`/`fix:`/`chore:`/
  `test:`/`docs:` prefix, a lowercase sentence subject describing the resulting
  state, a substantial body saying who decided and when, what was wrong, what
  evidence backs it, and what was deliberately left out. Last line is
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- **After every branch change, run the duplicate-file check** at the end of
  this plan. This folder is inside iCloud Drive and branch changes have made
  silent conflict copies once already.
- Run the whole suite with `python3 -m pytest`. It was **1198 passed, nothing
  skipped** when this plan was written. If `app/web/dist` is older than
  `app/web/src`, 57 tests skip: run `cd app/web && npm run build` first.

## The work list

Tick a box only when its tests pass. `app/tests/test_plans_delete_themselves.py`
reads these boxes: when every one is ticked, this plan is finished and the test
fails until it is deleted. That is deliberate.

### Slice 1, the captions cannot be lost

- [x] Write `app/tests/test_captions_are_never_lost.py` and watch it fail
- [x] Add `app/server/captionbackup.py`
- [x] Keep the previous version, then write through `state.write_text`, in `save_manifest`
- [x] The whole suite passes and nothing skips
- [x] Commit on `captions-cannot-be-lost`, and Spenser says yes

### Slice 2, the app writes a log

- [x] Write `app/tests/test_the_log.py` and watch it fail
- [x] Add `app/server/applog.py`, with rotation and the key guard
- [x] Add `RRF_LOG_FILE` to `never_touch_the_real_home` in `app/tests/conftest.py`
- [x] Record every request, and the cost of the manifest read by name
- [x] Record the four places that currently swallow an error in silence
- [x] Add `Show the log` to the Settings screen
- [x] The whole suite passes and nothing skips
- [x] Commit on `the-app-writes-a-log`, and Spenser says yes

### Ship 0.6.1, and what actually happened

- [x] Build the interface, set `VERSION` to 0.6.1, run the suite green
- [x] Cut the package and upload the three files, `latest.json` last
- [x] Spenser presses the update button on his Windows virtual machine
- [x] **It failed, and finding out why took the rest of the night.** Two faults
      were stacked in front of the bucket, neither of them in this plan:
      certificates the embedded Python would not trust, shipped as 0.6.2, and a
      name Cloudflare refuses, shipped as 0.6.3. **The update check had never
      once worked, on any machine, in any version.**
- [x] 0.6.3 installed by hand on the virtual machine and running
- [ ] The office takes it. **Superseded: 0.6.4 goes instead, carrying the rest
      of this plan.**

### Slice 3, each capture date is read once

- [x] Write `app/tests/test_capture_dates_are_read_once.py` and watch it fail
- [x] Add `app/server/capturedates.py`
- [x] Give `exif_order` its optional `stamp_for`, leaving the default as today
- [x] Pass the cached reader from `load_manifest` and `upload_photos`
- [x] **Not in the plan and worse than what was: `caption-estimate` re-encoded
      every waiting photograph on every click.** That is what Colleen's
      eleven-second waits actually were. `plan_tranches` now takes the same
      kind of reader.
- [x] The whole suite passes and nothing skips
- [ ] Commit on `read-each-date-once`, and Spenser says yes

### Slice 4, the screen says what it is doing, and never lies about it

- [x] Add the second keyspace to `app/server/progress.py`
- [x] Report from `load_manifest`, and add `GET /api/jobs/{name}/reading`
- [x] Poll from mount and show the count in place of `Loading...`
- [x] **B6: show the error instead of `Loading...` for ever.** The screen
      already catches the failure and stores it, then returns `Loading...` at
      `PhotosScreen.jsx:216`, above every line that could display it. Colleen
      sat in front of that on 2026-09-03 with the answer in the app's pocket.
- [x] Add the cases to `app/web/src/screens/PhotosScreen.test.jsx`, including
      a manifest read that fails
- [ ] The whole suite passes and nothing skips
- [ ] Commit on `say-what-it-is-doing`, and Spenser says yes

### Slice 5, the folder the report uses is the folder photographs go into

**This is four bugs with one cause.** `store_upload` always writes to the top
of `Photos`; `_report_set` only keeps what is in the chosen folder. So the app
puts a photograph where the report cannot see it, and everything afterwards
treats it as an outsider. Spenser worked that out from the behaviour alone on
2026-09-03.

- [x] Add the failing cases to `app/web/src/screens/PhotosScreen.test.jsx`
- [x] Test for absence rather than emptiness, in both places
- [x] **B1, B2, B3, B5: `Add a photo` writes into the folder the report is
      pointed at**, not the top of `Photos`
- [x] A server test proving an added photograph survives a caption run, a
      take-out of a different photograph, and a build
- [x] A server test proving taking one out leaves no second copy anywhere
- [x] **B4: a door out of the blocked build.** Name the photograph that cannot
      be found and offer to take it out and carry on, rather than refusing with
      nothing to do. `Clear captions` must stop being blocked by the same
      check, because being unable to start over is worse than the first fault.
- [x] The whole suite passes and nothing skips
- [ ] Commit on `unstick-the-photo-folder`, and Spenser says yes

### Ship 0.6.4, carrying slices 3, 4 and 5 together

Spenser's call, 2026-09-03: finish the plan, ship it as one version, then
start again from the new lists.

- [ ] Build the interface, run the suite green
- [ ] Cut the package and upload the three files, `latest.json` last
- [ ] **Run `docs/CHECKS.md` on the virtual machine.** Checks 1 to 7 are the
      bugs this version claims to fix.
- [ ] Only then does the office take it

### Closing this plan out

- [ ] Prove slices 1, 3 and 4 by hand on the Blaul job, not only by test
- [ ] Ask Spenser, then fold the learnings into `docs/ROADMAP.md`
- [ ] Ask Spenser, then tick the finished items out of `docs/PUNCHLIST.md`
- [ ] Delete this plan


## Slice 1: the captions cannot be lost

**Branch:** `captions-cannot-be-lost`

**Goal.** The file holding the captions is never half written, and the previous
version is always recoverable.

**Why.** `app/server/photos.py:372` is the only line in the app that writes
`photo-manifest.json`, and it is a plain `path.write_text(...)`. There is no
temp file and no copy. `save_manifest` also reads that same file first, to
recover entries the screen was not shown, so a crash mid-write destroys the
merge source as well as the target. Seven routes reach that line, and one of
them, the caption run at `app/server/main.py:820`, writes once per tranche
inside the loop. That is the write that persists work Spenser paid for.

**Reuse, do not invent.** `app/server/state.py:103` `write_text(path, text,
owner_only=False)` already does exactly the right thing: temp file created in
the destination's own directory, UTF-8, `newline="\n"`, `flush` + `fsync`,
then `os.replace`, with the temp file removed and the real file untouched on
any failure. `state.py:73` `_guard` refuses to write through a symlink. Nine
modules already use it.

**Do not use `state.write_json` here.** It stamps a `schema` key into the
payload. `photo-manifest.json` lives in Mark's job folder, is hand-editable by
design, and is read raw by `photo_pages.build_photo_docx`, `_set_cut`,
`clear_captions` and `main.py:996`. `write_text` is the correct fit.

### What to do

1. **New module `app/server/captionbackup.py`.** It lives under `app/server/`,
   which `tools/package_windows.py` copies wholesale, so packaging needs no
   change.

   - `spare_for(photos_dir: Path) -> Path`, returning
     `thumbcache.cache_root() / "captions" / ("%s.json" % fingerprint)`, where
     the fingerprint is the first 16 hex of the sha256 of the resolved
     `photos_dir`. **Reuse `thumbcache._fingerprint` and `thumbcache.cache_root`
     rather than writing new ones** (`app/server/thumbcache.py:58,65`).
   - `keep(photos_dir: Path, current_text: str) -> None`, writing that text to
     `spare_for(...)` through `state.write_text`. Swallow `OSError` and
     `StateUnreadable`: **failing to keep a spare must never stop a save.**
   - One spare per job, overwritten each time. Bounded by the number of jobs,
     so no pruning is needed.

   A `captions/` folder under the cache root does not match
   `thumbcache.OWNED_FOLDER` (`^[0-9a-f]{16}$`), so `thumbcache.prune` skips it
   entirely. That is deliberate and it is why the spare is not put inside an
   existing fingerprint folder: `prune` treats any file that is not
   `*-<8hex>.jpg` as a stray and would then refuse to reclaim that folder's
   thumbnails for ever (`thumbcache.py:162-168`).

2. **Change `app/server/photos.py` `save_manifest`.** Immediately before the
   write, read the current file's text if it exists and hand it to
   `captionbackup.keep`. Then replace line 372 with
   `state.write_text(path, json.dumps(out, indent=2))`.

   Keep the body byte-identical to today (`json.dumps(out, indent=2)`, no
   trailing newline) so the file's shape does not change. The encoding becomes
   explicitly UTF-8, which it was not, and that is a fix in itself: Windows
   would otherwise pick a codepage that mangles an accented folder name.

3. **Do not touch the seven callers.** One choke point is the whole point.

### Tests

New file `app/tests/test_captions_are_never_lost.py`. Model it on
`app/tests/test_photos_api.py:20-25` for the client fixture.

- A save writes the spare, and the spare holds what the file held **before**
  the save.
- Two saves in a row leave the spare holding the second-to-last version.
- A write that raises part way leaves the original file exactly as it was.
  Force it by monkeypatching `state.write_text` to raise.
- No `.writing` temp file survives a failed save.
- A caption typed on a photograph outside the chosen folder still survives a
  save, which is the behaviour `save_manifest` already has. This is a
  regression guard, not new behaviour.
- The spare never lands inside the job folder. Assert its path is under
  `thumbcache.cache_root()`.

`app/tests/conftest.py:76` `never_touch_the_real_home` already sets
`RRF_CACHE_DIR`, so the spare is contained in tests with no change there.

**Commit:** `fix: the captions survive a bad write, and the last version is kept`

## Slice 2: the app writes a log

**Branch:** `the-app-writes-a-log`

**Goal.** When the screen sits, there is a file that says what the app was
doing and how long each step took.

**Why.** There is no logging anywhere in this codebase. A repo-wide search for
`import logging`, `getLogger` and `basicConfig` returns one hit, and it is the
`log_level="warning"` keyword at `app/run_app.py:164`, which with
`access_log=False` turns the request record off. Several places swallow
exceptions on purpose and keep no record at all: `run_app.py:57-61`,
`run_app.py:126-131`, `run_app.py:146-151`, `main.py:855-858`.

**Decision, reversible by Spenser.** The log may name the job and the file,
because it never leaves her machine on its own and that is what makes it
useful. A test forbids anything key-shaped from reaching it.

### What to do

1. **New module `app/server/applog.py`.**

   - `log_file() -> Path`, following the exact three-line shape every other
     app-owned path uses (`app/server/workspace.py:58`, `jobfacts.py:31`,
     `thumbcache.py:58`): `Path(os.environ["RRF_LOG_FILE"])` if set, else
     `Path.home() / ".rrf-app.log"`.

     **It must not live inside the program folder.** `packaging._walk` hashes
     everything under the package root and `packaging.verify` would fail on a
     file that changes (`app/server/packaging.py:177,282`).

   - `note(message: str, **fields) -> None`. One line per call: an ISO
     timestamp, the message, then `key=value` pairs. Appends. Never raises:
     wrap the whole body in `try/except Exception: pass`, because a logger that
     can take the app down is worse than no logger.
   - Rotate at 1 MB, keeping one previous file as `.rrf-app.log.1`. Nobody
     tends this machine, so an unbounded file is a slow leak.
   - `redact(text)` used on every value: refuse anything matching `sk-ant`
     or a long unbroken run of key-like characters, replacing it with
     `[removed]`.

2. **Record requests.** In `app/server/main.py` `create_app`, add one
   middleware that logs method, path, status and elapsed milliseconds. Keep
   `log_level="warning"` and `access_log=False` in `run_app.py` as they are:
   this is our own file, not uvicorn's console noise, and Mark's window stays
   quiet.

3. **Record the expensive step by name.** In `app/server/photos.py`
   `load_manifest`, log how many files it is about to open and how long the
   `exif_order` call took. That single line is what will settle whether her
   20 minutes is this code or something else.

4. **Record what is currently swallowed.** At `run_app.py:57-61`,
   `run_app.py:126-131`, `run_app.py:146-151` and `main.py:855-858`, keep the
   `except` and add an `applog.note` inside it. The behaviour does not change.
   The silence does.

5. **A button that shows it.** On the Settings screen, add `Show the log`,
   which opens the folder holding it. Reuse the existing reveal route that
   `PhotosScreen.jsx` already calls through `api.reveal`. One click, no
   typing, no email attachment hunt.

### Tests

New file `app/tests/test_the_log.py`.

- A request writes one line naming the method, the path and a duration.
- `RRF_LOG_FILE` is honoured, so nothing reaches the real home folder.
- A key never reaches the log. Pass `sk-ant-` strings through `note` and every
  field and assert they do not appear in the file. **This is the Never list
  turned into a test.**
- The file rotates at the ceiling and keeps exactly one previous file.
- `note` never raises, even when the path is unwritable.

**Add `RRF_LOG_FILE` to `app/tests/conftest.py:76` `never_touch_the_real_home`.**
That fixture's own comment says the list is kept complete rather than added to
one test at a time.

**Commit:** `feat: the app writes down what it did, so a hang leaves evidence`

## Ship 0.6.1

After slices 1 and 2, on `working`, with Spenser's yes at each step.

1. `cd app/web && npm run build`
2. Set `VERSION` to `0.6.1`.
3. `python3 -m pytest`. Expect everything to pass and nothing to skip.
4. `python3 tools/package_windows.py`

   Produces `build/packages/Roy R. Fisher v0.6.1/`, the matching `.zip`, its
   `.sha256` sidecar, and `latest.json`.
5. Upload the three files to the `rrf-app-updates` bucket. **`latest.json`
   last**, because it is what announces the version and nothing should point at
   a zip that is not there yet. The script prints this instruction itself.
6. **Gate: Spenser presses the update button on his own Windows virtual
   machine and it works.** The button has never run on Windows. 0.6.0 carries
   it, so 0.6.1 is the first version anyone can take by pressing it. If it
   fails, the zip and `Install or update Roy R. Fisher.bat` remain the
   fallback and she is no worse off.
7. Only then does the assistant take it.

## Slice 3: each capture date is read once

**Branch:** `read-each-date-once`

**Goal.** Opening the photo screen and clicking a button stop re-opening every
photograph.

**Why.** `app/engine/photo_pages.py:82` `exif_order` opens every file it is
given, to read its capture date, and the answer is thrown away. `load_manifest`
calls it at `app/server/photos.py:321` with every file on disk the manifest
does not know by name. On a cold job of 131 photographs that is 131 opens, and
it happens again on the next click, for ever, because
`load_manifest` never writes back. That is deliberate: its docstring says a
plain read must not have a side effect. **So the dates go in a cache beside the
list, never inside it.** The file holding the captions is then never opened for
writing by this change at all, which is why this slice cannot cost her a
caption.

### What to do

1. **New module `app/server/capturedates.py`.**

   - Storage: `thumbcache.cache_root() / "dates" / ("%s.json" % fingerprint)`,
     the fingerprint being the same 16 hex of the resolved Photos folder that
     `thumbcache.folder_for` uses. One file per job. Skipped by
     `thumbcache.prune` for the same reason as slice 1, which is correct here.
   - Shape: `{"<file name>": {"mtime": <float>, "stamp": "<exif string>"}}`.
   - `stamp_for(path: Path) -> str`: return the stored stamp when the stored
     `mtime` equals the file's current `mtime`, otherwise open the file, read
     the stamp, store it, and return it. Mtime is the same staleness rule
     `thumbcache.is_stale` already uses (`thumbcache.py:97`), so there is one
     rule in the app and not two.
   - Write through `state.write_text`. Treat every failure as a miss: a cache
     that cannot be written must still answer, just slowly.

2. **Give `exif_order` a way in without changing what it means.** Add an
   optional keyword to `app/engine/photo_pages.py:82`:
   `exif_order(paths, stamp_for=None)`, defaulting to today's inline read. The
   engine keeps no knowledge of the cache and its existing tests
   (`test_number_order.py`, `test_photo_pages.py`,
   `test_photo_pages_golden.py`) keep passing untouched.

3. **Pass the cached reader from the server.** At `app/server/photos.py:321`
   and `app/server/photos.py:519`, call
   `exif_order(new_files, stamp_for=capturedates.stamp_for(job))`.

4. **Leave the double call alone.** `GET /manifest` and
   `GET /caption-estimate` both call `load_manifest`, and after this slice both
   are cheap. Changing the screen's call pattern is slice 4's business, and
   mixing them makes both harder to prove.

### Tests

New file `app/tests/test_capture_dates_are_read_once.py`. **Model it closely on
`app/tests/test_thumbnails_do_not_rewalk.py`**, which exists for exactly this
kind of claim and whose docstring explains why: it counts calls rather than
measuring time, because a timing test passes for ever on a fast disk and says
nothing true about her machine.

Copy its `Counter` shape (`test_thumbnails_do_not_rewalk.py:54-63`): a
`monkeypatch.setattr` wrapper around `PIL.Image.open` that delegates to the
captured original and counts. Build the counter **after** the client and the
warm-up, so setup is not counted.

- A first load of a job of N photographs opens N files. Pin the number.
- A second load opens **zero**.
- A click of `Mark Reviewed` after that opens zero.
- Touching one photograph makes exactly one file be re-opened, not N.
- The order the app produces with the cache is identical to the order without
  it. Use `test_number_order.py:28,34` `plain()` and `stamped()` to build
  photographs with and without EXIF.
- A photograph whose stamp cannot be read still sorts by its name, as today.
- The cache never lands inside the job folder.

Synthesise photographs with PIL into `tmp_path`. **Do not lean on the private
corpus.** `conftest.py:19-24` records that a worktree once made 124 tests skip
silently, and a skip reads as proof when it is not.

**Commit:** `fix: a photograph's capture time is read once, not on every click`

## Slice 4: the screen says what it is doing

**Branch:** `say-what-it-is-doing`

**Goal.** She can tell a busy screen from a dead one.

**Why.** `app/web/src/screens/PhotosScreen.jsx:216` returns
`Loading...` and nothing else until the manifest arrives. A slow screen and a
broken screen look identical. The rule is already on record from 2026-08-28,
about the update download: a bar that says nothing looks like a hang, because
her jobs are on a network drive. The photo screen never got it.

### What to do

1. **A second keyspace for progress, not a second meaning for the first.**
   `app/server/progress.py` holds one entry per job and `start` replaces it.
   A manifest read beginning during a caption run would wipe that run's
   position, and the caption poller itself refetches the manifest
   (`PhotosScreen.jsx:111`), so the collision is real and not theoretical. Its
   field names (`requests`, `captioned`) are caption vocabulary and would lie.

   `app/server/updates.py:480` already set the precedent: it copied the shape
   rather than overloading the dict. Do the same. Add `_reads`, plus
   `read_start`, `read_advance`, `read_finish` and `read_state`, to
   `progress.py`, guarded by the existing lock.

2. **Report from where the work happens.** `load_manifest` calls
   `read_advance` as it walks the files it must open.

3. **A cheap route to poll.** `GET /api/jobs/{name}/reading`, returning
   `progress.read_state(name)`. It must not call `load_manifest`.

4. **Poll from mount, not from a click.** The existing caption poller is
   created inside `runCaptions` (`PhotosScreen.jsx:107`), so nothing is
   polling at mount, which is when this is needed. Start an interval alongside
   the manifest call at `PhotosScreen.jsx:30` and clear it when the manifest
   lands. Replace the bare `Loading...` at line 216 with the count:
   **`Reading photograph 40 of 131`**, falling back to `Loading...` when the
   count is not known yet.

   Spenser chose a count over a plain sentence on 2026-09-02.

### Tests

- Server: the route reports rising numbers during a load and zeroes after it,
  and a caption run in flight is not disturbed by a manifest read. Put these in
  the new `app/tests/test_capture_dates_are_read_once.py` or a sibling.
- Screen: **add cases to the existing
  `app/web/src/screens/PhotosScreen.test.jsx`**, which already has about 25.
  Spy on the new api function the way `beforeEach` at `:47-66` already spies on
  seven others. Assert the count renders while the manifest promise is unsettled
  and that the poller is cleared afterwards.

**Commit:** `feat: the photo screen counts what it is reading instead of sitting`

## Ship 0.6.2

Same six steps as 0.6.1, with `VERSION` set to `0.6.2`, and the same gate on
Spenser's virtual machine before the assistant takes it.

## Slice 5: the folder can be changed after it is picked

**Branch:** `unstick-the-photo-folder`

**Goal.** She can change which folder the report photographs come from, after
one has already been chosen.

**Why, proven 2026-09-02.** The chosen folder is stored in
`~/.rrf-job-facts.json`. For the Blaul job it is `""`, meaning the top of the
Photos folder, which is a real choice and not an absent one. Two places in the
screen read it as absent:

- `app/web/src/screens/PhotosScreen.jsx:578`,
  `{where && where.chosen && ( ... )}`. `""` is falsy, so the
  `Use a different folder` button never draws.
- `app/web/src/screens/PhotosScreen.jsx:226`,
  `needsFolder = !!where && (where.needs_choice || where.chosen_missing || asked)`.
  All three are false, and `asked` can only become true through the button in
  the first case, which does not exist.

The result: the report holds four photographs, two aerials, a sketch and
`Staircase.jpg`, while the 61 real ones sit in `RAW pics_425 Valley St,
Burlington (Blaul Lofts)` and are shut out.

**The server is already correct.** `app/server/main.py:580` compares against
`None`, not against emptiness. This is a screen fault only. It is last because
she cannot reach it until `Loading...` clears.

### What to do

In `app/web/src/screens/PhotosScreen.jsx`, test for absence rather than
emptiness in both places: `where.chosen !== null && where.chosen !== undefined`.

The screen already has the right words for the empty case. Line 262 renders
`The Photos folder itself` and line 580 does the same. Nothing new to write.

### Tests

Add cases to `app/web/src/screens/PhotosScreen.test.jsx`. Follow the shape at
`:76-79` (`show()` renders then awaits the heading) and the button assertions
at `:290-296`.

- With `chosen: ""`, the `Use a different folder` button is present.
- Clicking it opens the chooser and lists all three folders with their counts.
- Picking a different folder calls `api.putPhotoGroup` with that folder.
- With `chosen: null`, the chooser still opens on its own, as today.

**Commit:** `fix: the top of the Photos folder is a choice, not the absence of one`

## Ship 0.6.3

Same steps, `VERSION` set to `0.6.3`, same gate.

## Slice 6, sketched only: the log reaches Spenser on its own

Not approved to build. It needs a Cloudflare Worker that does not exist, so
that no password ships inside the package, and it moves client property
addresses off her machine. Both are Spenser's decisions and neither is settled.
Write no code for this until he opens it.

## Verification

Run all of this on `working` after each slice merges, and before any package
is cut.

1. `cd app/web && npm run build`
2. `python3 -m pytest`
   Baseline when this plan was written: **1198 passed, nothing skipped.**
   Each slice adds tests, so the number rises. Nothing may skip. If tests skip
   with `app/web/dist is stale`, step 1 was missed.
3. The duplicate-file check, after every branch change:

       python3 -c "import pathlib; skip={'node_modules','build','.git','TEST JOBS','.rrf-demo-baseline'}; d=[p for p in pathlib.Path('.').rglob('* 2.*') if not (skip & set(p.parts))]; print('duplicates:', len(d)); [print('  ',p) for p in d]"

   It must print `0`. This folder is inside iCloud Drive and a branch change
   made 12 silent conflict copies on 2026-09-02. They ran as 130 extra tests
   and nothing reported them.

4. **Prove slices 3 and 4 by hand, on the real job**, not only by test.
   `RRF_UPDATE_IN_CHECKOUT=1 python3 app/run_app.py`, open
   `ZZ-TEST_BLAUL LOFTS - captions and subfolders`, and watch the count appear
   and the second open be instant.

5. **Prove slice 1 by hand.** Caption a photograph, save, then look in
   `~/.rrf-app-cache/captions/` and confirm the spare holds the version before
   that save.

## The last task in this plan

Fold what was learned into `docs/ROADMAP.md`: the measured cost of a click, the
two defects and their shared shape, and whatever the log turns out to say about
her 20 minutes. Tick the finished items out of `docs/PUNCHLIST.md`. **Then
delete this plan**, because a finished work list is clutter the next session
reads as current. Ask Spenser before writing to either file.

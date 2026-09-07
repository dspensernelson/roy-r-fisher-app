# Plan: photo bands

## Context

Mark's office orders photo pages by dragging one thumbnail at a time. F6 in
`docs/FUTURES.md` replaces that with one click per photograph: Mark turns bands
on, clicks one dot under each photograph, and the pages come out arranged the
way the property reads.

**Approved by Spenser on 2026-09-07.** The design was written on 2026-09-02 and
sat unapproved until now. It is in `docs/FUTURES.md` under F6 and that entry,
not this plan, is the record of why bands are typed rather than a fixed list.

**One amendment to the design, Spenser 2026-09-07: the Reviewed tick sits at
the lower left of the tile**, with the band dots running to its right. F6 as
written put the tick at the end of the row as the last dot. Lower left is
better because the tick then keeps one fixed position however many bands a job
has, so it never moves under his cursor as he adds them.

**The dot row is always there, even with bands off**, holding just the tick.
That was the open question in F6 and this is the answer: one control and one
code path, rather than a button on some jobs and a dot on others.

### What is here today

- `app/server/photos.py:112` `included()` is the one place that says which
  photographs are in the report and in what order. Captions, the preview and
  the build all read it. Bands must not become a second ordering system that
  the build has to reconcile against this one.
- `app/web/src/screens/PhotosScreen.jsx:213` `drop()` reorders by moving
  entries between the slots the included photographs already occupy, so a cut
  photograph keeps its exact index and comes back to the same place.
- `app/web/src/screens/PhotosScreen.jsx:695` is the `Mark reviewed` button,
  inside `.review-line` (`app/web/src/brand.css:504`). It is per tile and there
  is deliberately no way to do all of them at once. That stays true.
- `app/web/src/screens/PhotosScreen.jsx:333` `allReviewed` gates the build.
  `app/server/photos.py:71` `review_progress` is the server's half of the same
  fact and `app/server/main.py:1079` refuses a build without it.
- `app/server/photos.py:557` `_validate_manifest_shape` is the only guard on
  what may be written into the manifest.

### The three constraints, from F6, which are the reason this works

1. **Turning bands on moves nothing.** Photographs already loaded sit in an
   unassigned strip and drain as Mark clicks. Build waits for the strip to
   empty, the same gate `allReviewed` already uses.
2. **A band click resorts `manifest["photos"]` itself**, so array order always
   equals band order then position within band. `included()` and
   `build_photo_docx` change not at all.
3. **A band's letter is assigned at creation and frozen.** First letter, then
   first two on collision, then three. Adding, renaming or deleting a band
   never relabels an existing one. Warehouse keeps W when Workshop arrives and
   takes Wo.

**These three belong in a docstring and a test, next to the one on
`included()`.** That is where they cannot drift from what they describe, and
slices 1 and 2 put them there.

### One thing to confirm before slice 3

F6 says three locked bands, A first, B middle, C last, and typed bands slide
anywhere between A and C. It does not say what the three are called or whether
a typed band may sit between A and B.

**Built to this assumption unless Spenser says otherwise:** A, B and C are
locked, cannot be deleted, keep their letters for ever and keep their order
relative to each other. A typed band may go anywhere strictly between A and C,
including before B. The three ship named `First`, `Middle` and `Last`, because
their position is their meaning, and Mark can rename any of them without the
letter changing.

**Ask before slice 3 starts.** Slices 1 and 2 do not depend on the answer.

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
- Run the whole suite with `python3 -m pytest`. If `app/web/dist` is older than
  `app/web/src`, 57 tests skip: run `cd app/web && npm run build` first.

## The work list

Tick a box only when its tests pass. `app/tests/test_plans_delete_themselves.py`
reads these boxes: when every one is ticked, this plan is finished and the test
fails until it is deleted. That is deliberate.

### Slice 1, the manifest can hold bands, and nothing behaves differently

- [ ] Write `app/tests/test_photo_bands.py` and watch it fail
- [ ] Add `bands_on`, `band_list`, `band_of` and `letter_for` to `app/server/photos.py`
- [ ] Put constraint 3 in `letter_for`'s docstring, with the Warehouse and Workshop case as its test
- [ ] Teach `_validate_manifest_shape` about `bands`, `bands_on` and a photo's `band`
- [ ] Prove a manifest with no bands reads as bands off, no bands, nothing to migrate
- [ ] The whole suite passes and nothing skips
- [ ] Commit on `the-manifest-holds-bands`, and Spenser says yes

### Slice 2, a band click resorts the list itself

- [ ] Add the failing cases to `app/tests/test_photo_bands.py`
- [ ] Add `sort_by_band(manifest)`, with constraint 2 in its docstring
- [ ] Add `POST /api/jobs/{name}/photos/{file}/band`, taking a letter or null
- [ ] A cut photograph keeps its band and sorts with it, so uncutting restores its place
- [ ] Prove `included()` returns the same list it does today when bands are off
- [ ] Prove a build after a band click produces the same document as the same order reached by dragging
- [ ] The whole suite passes and nothing skips
- [ ] Commit on `a-band-click-sorts-the-list`, and Spenser says yes

### Slice 3, the band list and the toggle, per job

- [ ] Ask Spenser the question under "One thing to confirm" above
- [ ] Add the failing cases to `app/tests/test_photo_bands.py`
- [ ] Add `PUT /api/jobs/{name}/bands`: turn on or off, create, rename, delete, reorder
- [ ] A, B and C cannot be deleted, relettered, or moved out of order
- [ ] Deleting a typed band returns its photographs to unassigned and moves nothing else
- [ ] Turning bands on reorders nothing, and turning them off reorders nothing
- [ ] The whole suite passes and nothing skips
- [ ] Commit on `the-band-list`, and Spenser says yes

### Slice 4, one dot row under every photograph

- [ ] Add the failing cases to `app/web/src/screens/PhotosScreen.test.jsx`
- [ ] Add `setPhotoBand` and `putBands` to `app/web/src/api.js`
- [ ] Replace the `Mark reviewed` button with the tick at the lower left of the row
- [ ] Band dots to the right of the tick, one per band, in band order, with bands off showing none
- [ ] Add the unassigned strip, and hold the build until it is empty
- [ ] Add `.band-dot` to `app/web/src/brand.css` next to `.review-line`, using the tokens in `brand/Roy R. Fisher Design System/tokens/`
- [ ] The whole suite passes and nothing skips
- [ ] Commit on `bands-on-the-screen`, and Spenser says yes

### Closing this plan out

- [ ] Prove it by hand on the Blaul job, not only by test
- [ ] Ask Spenser, then fold the learnings into `docs/ROADMAP.md`
- [ ] Ask Spenser, then mark F6 built in `docs/FUTURES.md`
- [ ] Delete this plan

---

## Slice 1: the manifest can hold bands

**Branch:** `the-manifest-holds-bands`

**Goal.** The manifest can carry a band list, a toggle, and a band on each
photograph. Nothing reads any of it yet, so nothing behaves differently.

**Why first.** Every later slice writes into this shape, and the shape is the
one thing that is expensive to change once a real job has it on disk.

**Where it goes.** `app/server/photos.py`, next to `is_cut` (line 47) and
`is_reviewed` (line 61), which are the two entries this copies. Both answer
"absent means the safe default", and band does the same: absent means
unassigned.

    manifest["bands_on"]   bool, absent means off
    manifest["bands"]      list of {"letter": "A", "name": "First",
                                    "locked": true}, in order
    entry["band"]          the letter, absent means unassigned

**`letter_for(name, taken)`.** First letter of the name, uppercased. If that is
taken, the first two. Then three. The test to write is the one in F6: a job with
`Warehouse` at `W` gains `Workshop`, and Workshop takes `Wo` while Warehouse
keeps `W`. Then rename Warehouse to `Storage` and prove it still answers to `W`,
because the letter is frozen at creation and a rename is not a creation.

**`_validate_manifest_shape` (line 557).** It is the only guard on what may be
written, and it is deliberately narrow. Add exactly three checks and no more:
`bands_on` is a bool if present, `bands` is a list of objects each with a
non-empty string `letter` and `name`, and a photo's `band` is a string that
names one of them or is absent. An unknown letter on a photograph is an error,
not a silent drop, for the same reason `_validate_manifest_shape` refuses a
photo whose file resolves outside Photos: quietly fixing a broken manifest hides
the fault that made it.

## Slice 2: a band click resorts the list itself

**Branch:** `a-band-click-sorts-the-list`

**Goal.** Clicking a band moves the photograph in `manifest["photos"]`, so the
array stays the one ordering fact in the app.

**Why this and not a sort at read time.** `included()` at line 112 is used by
captions, the preview and the build, and its docstring says those three can
never disagree. A sort applied at read time would mean the array on disk and
the order in the report are two different answers, and the next person to read
the manifest by hand would see the wrong one. Constraint 2 exists to stop that.

**`sort_by_band(manifest)`.** Stable sort of `manifest["photos"]` by the band's
position in `manifest["bands"]`, leaving position within a band exactly as it
was. Unassigned photographs sort after every band. With `bands_on` false it
returns the list untouched, which is what makes turning bands off reorder
nothing.

**The cut photograph.** F6 decided a cut photograph keeps its band and sorts
with it, so uncutting restores its place. That is a change to what `drop()`
promises today, where a cut photograph holds its index. Both are right in their
own mode, and the test has to pin down both: with bands off, cut keeps its
index; with bands on, cut sorts with its band.

**The endpoint.** `POST /api/jobs/{name}/photos/{file}/band` with a JSON body
of `{"band": "W"}` or `{"band": null}` to unassign. It follows `_set_reviewed`
at line 645 exactly: load, touch the one key, `busy.writing()`, save, return the
manifest. Refuse an unknown letter with 400 and a plain sentence.

**The proof that matters.** Build the same job twice, once ordered by dragging
and once by band clicks that produce the same order, and prove the two
documents are identical. That is what "bands are not a second ordering system"
means in practice.

## Slice 3: the band list and the toggle

**Branch:** `the-band-list`

**Goal.** Mark can turn bands on for a job, add the ones his property needs,
rename and delete them, and put them in the order the property reads.

**Do not start until Spenser has answered the question in Context.**

**The endpoint.** `PUT /api/jobs/{name}/bands`, taking the whole list and the
toggle, validated by the same `_validate_manifest_shape` and saved through
`save_manifest` so the captions backup covers it like everything else.

**What it must refuse.** Deleting A, B or C. Changing any band's letter.
Reordering that puts a typed band before A or after C. Reordering that puts B
before A or after C. Each refusal says what is wrong in one plain sentence.

**Deleting a typed band** removes it from the list and removes that letter from
every photograph carrying it, which returns them to unassigned. It moves
nothing else, and the test proves the other bands' photographs sit exactly
where they sat.

**Turning bands on and off.** On writes `bands_on` true and does nothing else.
Off writes it false and does nothing else. Neither one touches
`manifest["photos"]`. That is constraint 1 and it is the whole reason bands can
be turned on in the middle of a job.

## Slice 4: one dot row under every photograph

**Branch:** `bands-on-the-screen`

**Goal.** Under each thumbnail: the Reviewed tick at the lower left, then one
dot per band running to its right. One click per photograph.

**The tick.** It replaces the `Mark reviewed` button at
`PhotosScreen.jsx:695-699`. It calls the same `onReview` (line 157) and the
same two endpoints, keeps the same disabled state until a caption is written,
and keeps the same title text explaining why. **It is still one photograph at a
time.** There is still no way to tick them all, and F2 in `docs/FUTURES.md`, the
one that would add that, is a separate decision behind a warning.

**The dot row is always rendered.** With bands off it holds the tick and
nothing else. That is the answer to the question F6 left open and it is why
there is one code path rather than two.

**The unassigned strip.** Above the grid, holding every photograph with no
band, draining as Mark clicks. When it is empty it disappears. The build button
is held while it has anything in it, alongside `allReviewed` at line 333, with a
title saying which of the two is missing. An empty band still shows its header,
so Mark can see he owes it photographs.

**Colour comes from the tokens**, `brand/Roy R. Fisher Design System/tokens/`,
pointed at rather than copied. The brand red sat wrong in a memory file for
months because it was written out instead of pointed at.

**The risk this slice carries.** Spenser has already called this screen
confusing, and this adds a row of dots to every tile. F8 is the layout pass and
it is not specified, so this ships into the screen as it is and what it teaches
goes to `docs/ROADMAP.md` for F8 to use.

## Verification

Run all of this on `working` after each slice merges, and before any package
is cut.

1. `cd app/web && npm run build`
2. `python3 -m pytest`
   Baseline when this plan was written, measured on `working` 2026-09-07:
   **1279 passed, nothing skipped**, in 3 minutes 10 seconds.
   Each slice adds tests, so the number rises. Nothing may skip. If tests skip
   with `app/web/dist is stale`, step 1 was missed.
3. The duplicate-file check, after every branch change:

       python3 -c "import pathlib; skip={'node_modules','build','.git','TEST JOBS','.rrf-demo-baseline'}; d=[p for p in pathlib.Path('.').rglob('* 2.*') if not (skip & set(p.parts))]; print('duplicates:', len(d)); [print('  ',p) for p in d]"

   It must print `0`.

4. **Prove it by hand on the real job**, not only by test.
   `RRF_UPDATE_IN_CHECKOUT=1 python3 app/run_app.py`, open
   `ZZ-TEST_BLAUL LOFTS - captions and subfolders`, turn bands on, and confirm
   nothing moved. Then click a band under one photograph and confirm it moves
   into that band and the rest sit still.

## The last task in this plan

Fold what was learned into `docs/ROADMAP.md`: whether one click per photograph
actually beat dragging, what the dot row did to a screen already called
confusing, and anything the band vocabulary turned out to want. Mark F6 built
in `docs/FUTURES.md`. **Then delete this plan**, because a finished work list is
clutter the next session reads as current. Ask Spenser before writing to either
file.

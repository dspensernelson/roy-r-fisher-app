# Plan: the switch that turns bands on

## Context

Version 0.6.7 shipped photo bands with no way to switch them on. Mark has the
dot row under every photograph and it holds only the tick, because a job has
no bands until something calls `PUT /api/jobs/{name}/bands` and nothing on
screen does. Spenser shipped it that way on purpose on 2026-09-07, knowing the
office could not reach the feature.

**This plan is the screen, and only the screen.** Every server route it needs
already exists and is tested. Creating, renaming, deleting and reordering are
all one route taking the whole list, and putting a photograph in a band is
another. Nothing here adds a route.

**Approved by Spenser on 2026-09-07**, from the design below, which is his own
words plus two pieces he was asked about and settled.

### What Mark sees

**The control.** A pill on the photo screen, on the title's row with the other
actions: `Bands  On | Off`. Off is where every job starts. Hit On and the band
chips appear to the right of it: `(A) (B) (C) (+)`.

**Adding.** Hit plus. A small box opens. He types `Warehouse`. The chip shows
`W`. `Office` shows `O`. He never types or picks a letter: the app gives it,
once, and it never changes after that.

**Moving.** He drags a chip anywhere between A and C. A and C never move,
because their position is their meaning.

**Renaming and removing.** Clicking a chip opens a small step holding the name
in a box and a `Remove` button. Removing a band sends its photographs back to
waiting and moves nothing else. A, B and C have no `Remove`.

**Off.** The dots vanish and the ordering stops. Every band and every click he
made is kept, so On brings all of it back.

### Decided, and not to be rediscovered

- **Fresh each time.** Spenser, 2026-09-07. A new job starts with A, B and C
  only. The app does not remember Warehouse from the last job. Wanting that is
  a want, and it needs a store outside the job folder, so it is not here.
- **The letter is never chosen on screen.** `PUT /api/jobs/{name}/bands` gives
  a letter to any band arriving without one, and refuses a letter the job does
  not already have. That is what keeps a rename from silently repointing every
  photograph in the band.

## Rules for whoever executes this

Read `HOW-WE-WORK.md` and `docs/ROADMAP.md` first. They govern. In particular:

- **One branch per slice.** Commits on it are recovery checkpoints and are
  allowed, because this plan is approved. **Nothing is pushed, merged, or
  delivered without Spenser saying yes.**
- **Never write into `Report Examples/`. Never move, print or log a key.**
- **No em dashes.** Anywhere. Hyphens instead.
- **Python 3.9 compatible.** No `int | None`, no `match`.
- **Test first.** Write the failing test, watch it fail, then fix it.
- **A test that passes before the code exists is testing nothing.** This
  happened four times in the bands work, always by asserting on absence. Assert
  that the click landed, not only that nothing moved.
- **Do not create any markdown file, doc or note this plan does not name.**
- Commit style, matching the last thirty commits: a `feat:`/`fix:`/`chore:`/
  `test:`/`docs:` prefix, a lowercase sentence subject describing the resulting
  state, a substantial body saying who decided and when, what was wrong, what
  evidence backs it, and what was deliberately left out. Last line is
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- **After every branch change, run the duplicate-file check** at the end of
  this plan.
- Run the whole suite with `python3 -m pytest`. Baseline on `working` when this
  plan was written, against the built 0.6.7 archive: **1314 passed, nothing
  skipped.** If tests skip saying the archive is not built, that is the
  packaging tests and it is expected until a package is cut.

## The work list

Tick a box only when its tests pass. `app/tests/test_plans_delete_themselves.py`
reads these boxes: when every one is ticked, this plan is finished and the test
fails until it is deleted.

### Slice 1, the pill, and the chips that appear with it

- [ ] Add the failing cases to `app/web/src/screens/PhotosScreen.test.jsx`
- [ ] Add the pill to the title's row: `Bands` with `On` and `Off`
- [ ] `On` calls `putBands` with the switch, and A, B and C arrive
- [ ] `Off` calls it again and the dots go, with every band and click kept
- [ ] Show the chips for A, B and C to the right of the pill while it is on
- [ ] Add the styles to `app/web/src/brand.css` next to `.band-dot`
- [ ] The whole suite passes and nothing skips
- [ ] Commit on `the-bands-switch`, and Spenser says yes

### Slice 2, the plus, and the name he types

- [ ] Add the failing cases to `app/web/src/screens/PhotosScreen.test.jsx`
- [ ] Add the plus chip, which opens a box for the name
- [ ] Typing `Warehouse` and confirming sends the whole list with the new name and no letter
- [ ] The chip comes back showing `W`, and a second band called `Workshop` shows `Wo`
- [ ] An empty name adds nothing, and the box closes on cancel
- [ ] The new chip lands between A and C, never outside them
- [ ] The whole suite passes and nothing skips
- [ ] Commit on `the-plus-and-the-name`, and Spenser says yes

### Slice 3, dragging a chip, and the step behind a click

- [ ] Add the failing cases to `app/web/src/screens/PhotosScreen.test.jsx`
- [ ] Drag a chip to a new place, and send the whole list in that order
- [ ] Dropping a chip before A or after C changes nothing and says why
- [ ] Clicking a chip opens a step holding its name and `Remove`
- [ ] A new name keeps the letter, proved on a photograph already in that band
- [ ] `Remove` sends that band's photographs back to waiting and moves nothing else
- [ ] A, B and C show no `Remove`
- [ ] The whole suite passes and nothing skips
- [ ] Commit on `move-rename-remove`, and Spenser says yes

### Closing this plan out

- [ ] Prove it by hand on the Blaul job, not only by test
- [ ] Ask Spenser, then fold the learnings into `docs/ROADMAP.md`
- [ ] Delete this plan

---

## Slice 1: the pill, and the chips that appear with it

**Branch:** `the-bands-switch`

**Goal.** Mark can turn bands on and off for a job, and see which bands it has.

**Where it goes.** `app/web/src/screens/PhotosScreen.jsx`. The actions row is
`screen-actions` and holds `Build photo pages` and `Generate captions` today.
The pill goes with them, because it is an action and actions sit on the
title's row.

**What it calls.** `putBands(job, { bands_on: true })` and
`putBands(job, { bands_on: false })`, already in `app/web/src/api.js`. The
route seeds A, B and C the first time the switch goes on and never seeds them
again. Turning the switch off writes the switch and touches nothing else, so
his clicks survive it. Both behaviours have server tests already, in
`app/tests/test_photo_bands.py`.

**What must not happen.** Turning the switch on must move no photograph. That
is constraint 1 of F6 and the server holds it, but the screen has to redraw
from the manifest the route returns rather than sorting anything itself.

## Slice 2: the plus, and the name he types

**Branch:** `the-plus-and-the-name`

**Goal.** Mark adds the bands his property needs, by name.

**How it talks to the server.** The whole list goes in one `putBands`, with
the new band as `{"name": "Warehouse"}` and no letter. The server gives the
letter. The screen must never send a letter for a band it is creating, and
never invent one to display before the answer comes back: the letter it would
guess and the letter it gets can differ, and the one on the photographs is the
server's.

**The collision case is already proved on the server.** Warehouse takes `W`,
then Workshop takes `Wo`. The screen only has to show what comes back.

## Slice 3: dragging a chip, and the step behind a click

**Branch:** `move-rename-remove`

**Goal.** Mark puts his bands in the order the property reads, renames one, or
takes one away.

**Dragging** reuses the pattern already in this file: `drop(i)` at
`PhotosScreen.jsx:213` reorders photographs by moving entries between the slots
they occupy. The chips are a smaller version of the same thing, and the new
order goes to `putBands` as the list order.

**Before A or after C is refused by the server**, with a plain sentence. The
screen shows that sentence rather than silently snapping the chip back, because
a control that undoes itself with no reason given is the fault this app keeps
writing down.

**The step behind a click** is the `.confirm` shape already used by
`resetStep` in `App.jsx:156-169`: a box naming what happens, with the action
and a Cancel. Removing a band is not a confirm on its own, but it does take
photographs out of their band, so the box says how many will go back to
waiting before he presses Remove.

## Verification

Run all of this on `working` after each slice merges, and before any package
is cut.

1. `cd app/web && npm run build`
2. `python3 -m pytest`
   Nothing may skip, except the packaging tests when no package is built.
3. The duplicate-file check, after every branch change:

       python3 -c "import pathlib; skip={'node_modules','build','.git','TEST JOBS','.rrf-demo-baseline'}; d=[p for p in pathlib.Path('.').rglob('* 2.*') if not (skip & set(p.parts))]; print('duplicates:', len(d)); [print('  ',p) for p in d]"

   It must print `0`.

4. **Prove it by hand on the real job.** Open
   `ZZ-TEST_BLAUL LOFTS - captions and subfolders`, turn the switch on, add
   `Warehouse`, confirm the chip shows `W`, drag it, rename it `Storage`, and
   confirm a photograph clicked into it is still in it afterwards.

## The last task in this plan

Fold what was learned into `docs/ROADMAP.md`: whether one click per photograph
beat dragging once Mark could actually reach it, and what the band names his
office typed turn out to be. That last one is the measurement F6 said nobody
had, and this is the first version that can produce it. **Then delete this
plan.** Ask Spenser before writing to the roadmap.

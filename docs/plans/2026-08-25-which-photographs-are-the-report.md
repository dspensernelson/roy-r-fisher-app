# Which photographs are the report

Written 2026-08-25 with Spenser, after Mark's first real session on his own
Windows PC. Branch: `photo-folder-choice`, cut from `windows-photo-pilot`.

**This plan deletes itself.** Task 8 is its own destruction, and it runs after
the debrief has folded what was learned back into `HOW-WE-WORK.md` and the
roadmap. A plan is a work list. Work lists are finished and thrown away.
Decisions and evidence live in the durable files, never in here.

## Why this exists

Mark installed the app and pointed it at his real jobs. The jobs were found.
Almost no photographs were. The photographs were plainly visible in the folder
listing and there was no way to get them into the report.

Measured afterwards, read only, on 2026-08-24 and 2026-08-25:

- The shipped version reads only the top layer of `Photos`. Mark's
  photographs sit one and two folders below it. On the Maquoketa job that is
  one photograph found out of 33, and the one found is the aerial.
- Every job in the corpus keeps its photographs twice: full size, and a
  hand-shrunk set. Eleven jobs, nine different folder namings: `Original`,
  `Raw pics_`, `Minimized`, `full size`, `Building`, `Used`, `Reduced`,
  `3525`/`3575`, `Report Photos_`. A new helper in Mark's office has just
  added a tenth. **No rule can be written against these names.**
- The shrinking is done by hand and the app already does it better. From a
  4032 x 3024 original the app embeds 1600 x 1200, which is 400 dots per inch
  at four inches wide. The helper's copy is 1008 x 756, which is 252. The app
  never enlarges, so his step permanently costs quality.
- The shrinking strips the EXIF. That is why he numbers the files: resizing
  destroyed the only record of the order they were taken in.
- Sorted as text, his numbering builds the report in the order
  1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9.

## What is being built

Spenser's model, in his words: **the left is the world, the right is what we
action on.**

The left, the job screen's folder listing, is an unfiltered index of
everything in the job. It already behaves this way and nothing here changes
it.

The right, Subject Photographs, is the report.

1. When he opens Subject Photographs and the job's photographs sit in more
   than one place, the app asks once which one holds the report photographs.
2. He picks. Those, and only those, are the report.
3. Any single file can still be added from the left by classifying it as a
   subject photograph. That is the straggler that never got copied across.

The app never reads a folder name for meaning. It shows him the folders his
own office made and he says which. That is what survives his helper inventing
an eleventh convention next month.

## Out of scope, named so it is not assumed

- No rule about what any folder name means. Not `Raw`, `Report`, `Used`,
  `Do Not Use`, `Minimized`, or a `Z` prefix.
- No change to cut and uncut, captions, review state, cost, building, output
  naming, or the AI policy.
- The general bulk classify for the other eight labels is **deferred, not
  dropped**. It was Spenser's original ask and it is a separate slice.
- Nothing is packaged or sent to Mark inside this plan.

## Global constraints

- `HOW-WE-WORK.md` governs. Its Never list has no judgement in it.
- Python 3.9 compatible: no `int | None` unions, no `match`.
- No em dashes anywhere: code, comments, tests, UI copy.
- Never write into `Report Examples/`, `locker/`, or any job folder of Mark's.
  The corpus is read only and every test that touches it proves so.
- The suite must end green after every task:
  `python3 -m pytest app/tests -q` and `cd app/web && npx vitest run`
- Baseline measured 2026-08-24 before this plan: **924 passed, 0 skipped**
  (Python) and **35 passed** (Vitest).
- Commits on this branch are recovery checkpoints. Nothing is pushed, merged,
  packaged, or delivered without Spenser's yes.

---

### Task 1: The new standing rule

Spenser put this rule forward on 2026-08-25. It governs beyond this plan, so
it lands in the rules file first and does not wait for the work to finish.

**Files:** `HOW-WE-WORK.md`

- [ ] **Step 1: Add it under Working style**

After the paragraph beginning "While a slice is still being understood", add:

```
Every plan destroys itself. A plan is a work list, and a finished work list
is clutter that the next session reads as current. The last task in any plan
is to fold what was learned into these files and then delete the plan. What
is worth keeping is a decision or a measurement, and neither of those lives
in a plan.
```

- [ ] **Step 2: Commit**

```bash
git add HOW-WE-WORK.md
git commit -m "docs: plans destroy themselves once their learnings are folded back"
```

---

### Task 2: Commit the subfolder walk

Already written, already tested, sitting uncommitted since 2026-08-24. It is
the floor everything else stands on. It is committed unchanged, as its own
commit, so that if anything later is reverted this survives on its own.

**Files:** `app/server/jobs.py`, `app/server/photos.py`,
`app/engine/photo_pages.py`, `app/web/src/screens/PhotosScreen.jsx`,
`app/web/src/brand.css`, `app/web/src/screens/PhotosScreen.test.jsx`,
`app/tests/test_photos_in_subfolders.py`,
`app/tests/test_recognition_against_real_jobs.py`, `VERSION`

- [ ] **Step 1: Create the branch and confirm the tree is what was reviewed**

```bash
git checkout -b photo-folder-choice
git status --short
```

Expected: exactly the eight modified files and the one new test file above,
and nothing else. **If anything else appears, stop and report.**

- [ ] **Step 2: Run both suites before committing**

`python3 -m pytest app/tests -q` then `cd app/web && npx vitest run`
Expected: 924 passed and 35 passed. A different number is not automatically
wrong, but it must be explained before the commit, not after.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "fix: photographs are found wherever inside Photos they sit"
```

---

### Task 3: One job's answers, without losing the others

`jobfacts.py` already holds app-owned answers about a job, keyed by resolved
job path, in the home folder. The folder choice is another such answer, so it
goes there rather than into a fifth state file.

**One defect must be fixed on the way in.** `jobfacts.save` currently replaces
the whole entry for a job with just city and address. Adding a key beside
them without changing that means the next city correction silently erases the
folder choice, and Mark's report quietly changes shape with no action from
him.

**Files:**
- Modify: `app/server/jobfacts.py`
- Create: `app/tests/test_jobfacts_photo_folder.py`

**Interfaces:**
- `jobfacts.photo_folder(job) -> Optional[str]`. The chosen folder as a POSIX
  path relative to `Photos`, `""` for the top of `Photos`, and `None` when he
  has not chosen. `None` and `""` are different answers and must stay so.
- `jobfacts.save_photo_folder(job, folder: str) -> None`
- `jobfacts.forget_photo_folder(job) -> None`
- `jobfacts.save(job, city, address)` keeps its signature and stops discarding
  keys it does not know about.

- [ ] **Step 1: Write the failing tests**

Create `app/tests/test_jobfacts_photo_folder.py` covering:

- A saved folder round-trips.
- `""` round-trips as the top of `Photos` and is not confused with `None`.
- Saving a folder leaves an existing city and address untouched.
- Saving a city and address leaves an existing folder choice untouched.
- Forgetting the folder leaves city and address alone.
- Two jobs of the same name under different parents keep separate answers.
- Nothing is written inside either job folder: fingerprint before and after.

- [ ] **Step 2: Run them and watch the merge tests fail**

`python3 -m pytest app/tests/test_jobfacts_photo_folder.py -v`
Expected: the round-trip tests may pass once the functions exist; the two
"leaves the other untouched" tests must fail before the merge fix, and that
failure is the point of this task.

- [ ] **Step 3: Implement**

Make `save` merge over the existing entry rather than replace it, and keep the
existing "blank means no correction" behaviour for city and address. Add the
three folder functions. `for_job` must stop filtering out keys it does not
recognise, or it will hide the folder from itself.

- [ ] **Step 4: Both suites, then commit**

```bash
git add app/server/jobfacts.py app/tests/test_jobfacts_photo_folder.py
git commit -m "feat: a job remembers which folder its report photographs are in"
```

---

### Task 4: Break the import circle

`photos.py` has to ask `classify.py` a question in Task 6. The imports run in
a circle today: `classify` reads `inventory`, and `inventory` borrows one
confinement helper from `photos`.

`jobs.py` already carries an identical helper, `resolve_confined`, and
`inventory` already imports `jobs`. Pointing it there removes the circle with
no new code.

**One behaviour difference, named rather than buried:** the `jobs.py` version
also catches an operating system error, so an unreadable path becomes a
skipped file instead of a raised exception. That is better on Mark's machine
and it is a change.

**Files:**
- Modify: `app/server/inventory.py` (the import and its three call sites)
- Modify: `app/tests/` only if an existing test names the old import

- [ ] **Step 1: Change the import and the three call sites**

- [ ] **Step 2: Prove the circle is gone**

```bash
python3 -c "import sys; sys.path.insert(0,'app/server'); import photos, classify, inventory; print('ok')"
```

- [ ] **Step 3: Full suite, then commit**

```bash
git add app/server/inventory.py
git commit -m "refactor: inventory takes its confinement check from jobs, not photos"
```

---

### Task 5: Where a job's photographs actually sit

The app has to be able to say, for one job, what the candidate groups are.

**A group is the full folder path a photograph sits in, relative to `Photos`.**
Not the immediate child folder. Measured: Mason City's photographs are two
levels down, 50 in `Raw pics_Walmart Mason City 4151 4th St SW/All report
photos used` and 7 in `Raw pics_Walmart Mason City 4151 4th St SW/Do Not
Use`. Grouping by immediate child would make those one group and hand Mark the
seven he rejected.

**Files:**
- Modify: `app/server/photos.py` (add `photo_groups`)
- Create: `app/tests/test_photo_groups.py`

**Interfaces:**
- `photos.photo_groups(job) -> list` of
  `{"folder": str, "count": int, "sample": str}`, ordered with the largest
  group first and ties broken by folder name, so the folder most likely to be
  the report photographs is offered first. `sample` is one filename, for the
  thumbnail on the question. `folder` is `""` for the top of `Photos`.

- [ ] **Step 1: Write the tests**

- Maquoketa's shape: three groups, of 16, 16 and 1.
- Mason City's nested shape: two groups, of 50 and 7, and the group names are
  the full relative paths.
- Photographs loose in `Photos` and nothing else: one group, named `""`.
- An empty `Photos` folder: no groups, and no crash.
- Largest group first.
- Against the real corpus, read only, with a fingerprint proving nothing was
  written.

- [ ] **Step 2: Implement, run the full suite, commit**

```bash
git add app/server/photos.py app/tests/test_photo_groups.py
git commit -m "feat: the app can say where a job keeps its photographs"
```

---

### Task 6: The right side is what he picked

**Files:**
- Modify: `app/server/photos.py` (`load_manifest`), `app/server/main.py`
- Create: `app/tests/test_which_photographs.py`

**The rule, in full:**

- No choice recorded and one group or none: every photograph, exactly as
  today. **Every existing job and every existing test must be unaffected, and
  that is the main thing this task has to prove.**
- No choice recorded and more than one group: the app has no answer yet. The
  manifest is not the place that says so; the endpoint in the next task is.
- A choice recorded: the report is the photographs in that group, plus any
  file in the job classified `Subject photograph`, wherever it sits.
- The chosen group no longer exists, because the office renamed or moved it:
  no photographs, and the screen says plainly that the folder he chose is gone
  and offers the question again. **It must never silently fall back to another
  folder.**

The gate is applied where the manifest is read and again where captions are
generated and the document is built, each time from the stored answer, never
from what the browser sent.

**Two new routes in `main.py`:**

- `GET /api/jobs/{name}/photo-groups` returns
  `{"needs_choice": bool, "chosen": str or null, "chosen_missing": bool,
  "groups": [...]}`.
- `PUT /api/jobs/{name}/photo-group`, body `{"folder": "..."}`. Refuses with a
  400 any folder that is not currently one of that job's groups, so no choice
  can be recorded for a place the app has not just looked at.

- [ ] **Step 1: Write the tests**

Every bullet in the rule above, plus:

- A photograph classified `Subject photograph` from an unchosen group appears
  on the right.
- Removing that classification takes it off the right again.
- A caption typed on a photograph that is later outside the chosen group is
  kept, not deleted, and comes back with it if it is classified in.
- Cut, review, and build all act on the restricted list and not on the whole
  folder.
- A fingerprint of the job folder before and after proves nothing of Mark's
  was written.

- [ ] **Step 2: Implement, run the full suite, commit**

```bash
git add app/server/photos.py app/server/main.py app/tests/test_which_photographs.py
git commit -m "feat: the report is the photographs Mark picked"
```

---

### Task 7: The question on the screen, and the order

**Files:**
- Modify: `app/web/src/screens/PhotosScreen.jsx`, `app/web/src/api.js`,
  `app/web/src/brand.css`
- Modify: `app/web/src/screens/PhotosScreen.test.jsx`
- Modify: `app/engine/photo_pages.py` (`exif_order` fallback only)
- Create: `app/tests/test_number_order.py`

**The question.** When `needs_choice` is true, Subject Photographs shows the
question instead of the grid: one row per group, its exact folder name off the
disk, its count, and a thumbnail of its sample photograph. He picks one and
the grid appears. Once per job. A job with one group never sees it.

**When he has picked, the other groups are gone from the right.** Not greyed,
not counted, not collapsed. Spenser's call, 2026-08-25: the left is the world,
the right is what we action on. One quiet line says which folder the report
photographs came from, and a link re-opens the question.

**The order.** `exif_order` falls back to the filename when a photograph
carries no capture time, which is every photograph the office has shrunk. Make
that fallback read runs of digits as numbers, so `2` sorts before `10`.

**This changes only the fallback.** A photograph with a capture time is
ordered by it exactly as before, and there must be a test that says so.

- [ ] **Step 1: Write the tests**

Python, in `test_number_order.py`:
- `1, 2, 10, 11` sort in that order, not `1, 10, 11, 2`.
- Photographs carrying capture times are still ordered by them, and the
  numbering in their names does not override that.
- Names with no digits at all sort exactly as they did before.

Vitest, in `PhotosScreen.test.jsx`:
- `needs_choice` renders the question and not the grid.
- Each group shows its exact folder name and count.
- Picking one calls the endpoint and then renders the grid.
- One group renders the grid with no question.
- `chosen_missing` says the folder is gone and offers the question again.

- [ ] **Step 2: Implement**

- [ ] **Step 3: Build the interface and look at it**

```bash
cd app/web && npm run build && cd ../..
```

Then start the app and open the Maquoketa demo job, which has the real
two-folder shape. **A screen change gets a real screen review, so stop here
and show Spenser** before the commit.

- [ ] **Step 4: Both suites, then commit**

```bash
git add app/web app/engine/photo_pages.py app/tests/test_number_order.py
git commit -m "feat: the app asks once which folder holds the report photographs"
```

---

### Task 8: Debrief, fold back, and destroy this plan

In that order. The destruction is last and it is not optional.

- [ ] **Step 1: Run everything one final time and record the numbers**

`python3 -m pytest app/tests -q` and `cd app/web && npx vitest run`.
Record both summary lines. They are the numbers the report to Spenser quotes.

- [ ] **Step 2: Walk it front to back on a real job**

Open a job with one folder of photographs and a job with several. Confirm the
first never asks and the second asks once. Confirm the built document opens.
Confirm, by fingerprint, that no file of Mark's changed.

- [ ] **Step 3: Fold what was learned into the durable files**

Nothing from this plan survives except what is written here. Candidates,
each to be judged rather than copied:

- `docs/plans/2026-08-15-migration-roadmap.md`: the decision that the app
  never reads a folder name for meaning, and asks Mark instead.
- The same file: that the office's hand-shrinking is redundant and costs
  quality, with the measured numbers, because that is the case Spenser will
  make to Mark and it must not live only in a chat.
- `HOW-WE-WORK.md`: anything the build proved about how we work, including
  whether Task 1's new rule needs sharpening after its first use.
- `README.md`: the measured test count, if it moved.

- [ ] **Step 4: Report to Spenser**

The four-part Product Control Brief. Completed work, user experience,
decisions still needed, next move. Separate what was built from what is
proposed.

- [ ] **Step 5: Delete this plan**

```bash
git rm docs/plans/2026-08-25-which-photographs-are-the-report.md
git commit -m "chore: the plan is finished, so the plan is gone"
```

The work is in the commits. The decisions are in the durable files. This file
has nothing left to say and staying would only let a later session read a
finished list as a live one.

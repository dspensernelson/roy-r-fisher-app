# Bulk classify

Written 2026-08-25 with Spenser. Branch: `bulk-classify`, cut from
`photo-folder-choice`.

**This plan deletes itself.** Task 6 is its own destruction, after the debrief
has folded what was learned into `HOW-WE-WORK.md` and the roadmap.

## Why this exists

Mark classifies files one at a time. Open the folder, click Classify on a row,
pick a label. Two clicks per file. Mason City has 57 photographs in one folder,
so telling the app what they are is 114 clicks.

This was Spenser's first ask on 2026-08-25. It went out of scope by agreement
when the folder question turned out to solve the photographs case in one click,
and the roadmap records it as still owed. This is that debt.

## What is being built

Spenser's flow, with one change he approved.

1. He opens a folder on the left. Inside it, above the files, one link:
   **Bulk classify**.
2. He clicks it. Tick boxes appear on that folder's rows, with
   **Select all 16** beside them.
3. He ticks what he wants. The moment anything is ticked a bar appears:
   `3 selected · Classify these · Cancel`.
4. **Classify these** opens the same nine labels he already knows.
5. He picks one. It is applied to everything ticked, in one write.

**The change from what Spenser first described.** He suggested clicking
`Bulk classify` a second time to apply. That makes one control mean two things,
and the second meaning is the one that writes. So the applying action is its
own control, it says how many it is about to act on, and Cancel is a separate
word rather than the same button pressed twice.

**Nothing appears on a row until he asks for it.** No tick boxes on every file
in every folder for the ninety per cent of the time he is not doing this.

## Approved decisions, 2026-08-25. Do not reopen these.

- **A batch may half-succeed.** Ticking 16 files where 2 are PDFs and picking
  `Subject photograph` applies the label to the 14 that can take it and refuses
  the 2. Refusing all 16 because of 2 punishes him for the app's own rule.
- **The refused ones stay ticked, with their reason showing.** The ones that
  worked clear. So his next click can give the two that failed the label they
  actually deserve, without finding them again.
- **Ticks do not survive the folder closing.** One folder at a time. Selecting
  across several folders at once is a different feature and is not built until
  he has wanted it twice.
- **All nine labels.** This is bulk classify, not bulk-mark-photographs.
- **A file already classified is replaced**, the same as `Change` does today.

## Out of scope, named so it is not assumed

- No selection that spans folders.
- No new labels, and no change to the nine.
- No change to the single-file Classify path, which stays exactly as it is.
- No filename-based suggestion. That is a separate owed item in the roadmap
  and it needs its own measurement pass first.
- No layout pass. Also owed, also separate.

## Global constraints

- `HOW-WE-WORK.md` governs.
- Python 3.9 compatible: no `int | None` unions, no `match`.
- No em dashes anywhere.
- Never write into `Report Examples/` or `locker/`, and never into one of
  Mark's job folders. Classifications live in the app's own file.
- Both suites green after every task:
  `python3 -m pytest app/tests -q` and `cd app/web && npx vitest run`
- Baseline at branch point, measured 2026-08-25: **1,014 Python, 49 Vitest.**
- Commits are recovery checkpoints. Nothing pushed, merged, packaged or
  delivered without Spenser's yes.

---

### Task 1: Many files, one write

**Files:**
- Modify: `app/server/classify.py`
- Create: `app/tests/test_bulk_classify.py`

**Interfaces:**
- `classify.set_labels(job, rels: list, label: str) -> dict` returning
  `{"applied": [rel, ...], "refused": [{"file": rel, "reason": str}, ...]}`.
- One read of the store and one write, however many files. Fifty-seven
  separate reads and writes is fifty-seven chances to be interrupted halfway.
- A label outside the nine raises `ValueError` for the whole call. That is a
  programming error, not something one file can be wrong about.
- Per-file refusals use `classify.refusal`, which already exists and already
  carries the wording, so bulk and single can never disagree about why.
- A file the inventory does not currently hold is refused with a reason, never
  recorded.

- [ ] **Step 1: Write the failing tests**

Cover: many files one label; the store written once; a partial batch applying
the valid ones and refusing the rest with their reasons; nothing written for a
refused file; a bad label raising before anything is written; an empty list;
a file not in the job refused rather than recorded; another job's records
untouched; and a fingerprint proving nothing is written inside the job folder.

- [ ] **Step 2: Run them and watch them fail**

- [ ] **Step 3: Implement**

- [ ] **Step 4: Both suites, then commit**

```bash
git add app/server/classify.py app/tests/test_bulk_classify.py
git commit -m "feat: many files take one label in one write"
```

---

### Task 2: The route

**Files:**
- Modify: `app/server/main.py`
- Modify: `app/tests/test_bulk_classify.py`

`PUT /api/jobs/{name}/classifications`, body `{"files": [...], "label": "..."}`.

Returns `{"applied": [...], "refused": [{"file": ..., "reason": ...}]}`.

400 on a label outside the nine, and 400 on an empty list. The existing
single-file routes are not touched.

- [ ] **Step 1: Tests for the route, including the partial answer's shape**
- [ ] **Step 2: Implement**
- [ ] **Step 3: Both suites, then commit**

```bash
git add app/server/main.py app/tests/test_bulk_classify.py
git commit -m "feat: one call classifies many files"
```

---

### Task 3: The screen

**Files:**
- Modify: `app/web/src/api.js`, `app/web/src/screens/JobHome.jsx`,
  `app/web/src/brand.css`
- Modify: `app/web/src/screens/JobHome.test.jsx`

The bulk bar lives inside the opened folder, above its files, not in the
folder's header row. The header is already a button and a control inside a
control is not one.

Two states:

- Idle: one link, `Bulk classify`.
- Selecting: `Select all 16`, then once anything is ticked,
  `3 selected · Classify these · Cancel`.

`Classify these` opens the nine labels, the same list the single-file path
opens, drawn from the same endpoint so they cannot drift.

After applying: the ones that worked clear their ticks. The refused ones stay
ticked and each shows its reason on its own row, in the same place and the same
style the single-file refusal already uses.

Closing the folder leaves selecting mode and clears everything.

- [ ] **Step 1: Vitest first**

The link appears only on an opened folder. Clicking it shows tick boxes.
`Select all` ticks every file in that folder and no other. The bar shows the
true count. `Classify these` sends every ticked file with the one label.
Refused files stay ticked and show their reason; applied ones clear. `Cancel`
clears everything and leaves the mode. Closing the folder clears everything.
The single-file `Classify` still works while none of this is on screen.

- [ ] **Step 2: Implement**

- [ ] **Step 3: Build and look at it**

```bash
cd app/web && npm run build && cd ../..
```

Then run the app against the demo jobs and open Mason City's photo folder,
which is the 57-file case this exists for, and a folder holding a mixture of
PDFs and photographs, which is the partial case.

- [ ] **Step 4: The screen stop.** Commit, then STOP and ask Spenser to click
  through before Task 4.

---

### Task 4: Prove it on the real corpus

**Files:**
- Modify: `app/tests/test_bulk_classify.py`

Read only, against the real jobs, with a fingerprint before and after proving
nothing in them was written. One test that classifies a real folder's worth of
photographs in one call and checks the count, and one that runs a mixed folder
and checks the partial answer names the right files.

- [ ] **Step 1: Write them, run the full suite, commit**

---

### Task 5: Say the true number

**Files:**
- Modify: `README.md`

The suite count moves. Measure it after Task 4 and correct the line, then
verify the file against a run made after the edit rather than before it.

---

### Task 6: Debrief, fold back, and destroy this plan

In that order.

- [ ] **Step 1: Run both suites one final time and record both summary lines**
- [ ] **Step 2: Walk it front to back on a real job**
- [ ] **Step 3: Fold what was learned into the durable files.** The roadmap's
  "Still owed" list loses bulk classify and gains anything this turned up.
  `HOW-WE-WORK.md` gains anything the build proved about how we work.
- [ ] **Step 4: Report to Spenser.** The four-part Product Control Brief.
- [ ] **Step 5: Delete this plan**

```bash
git rm docs/plans/2026-08-25-bulk-classify.md
git commit -m "chore: the plan is finished, so the plan is gone"
```

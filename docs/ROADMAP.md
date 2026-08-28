# Roadmap: the locker system becomes the app

**This file does not delete itself.** Plans do, once their work is done and
their learnings are folded back into here. This is where those learnings land,
so it is the one document in the repository that is meant to grow. It lives
outside `docs/plans/` on purpose: everything in that folder is a work list with
a death date, and this is not one.

Written 2026-08-15 from a full review of both systems with Spenser. This is
the durable record of the shape and the decisions. It is context, not a work
list. Work lists are the phase plans beside this file, written one at a time
when a phase's edges are known.

## If you are an executor model reading this cold

Read in this order, before doing anything:

1. `HOW-WE-WORK.md` at the repo root. It governs. Its Never list has no
   judgement in it.
2. `README.md` at the repo root.
3. This file.
4. The phase plan you were handed.

Non-negotiables, repeated here because they are cheap to repeat and
expensive to miss:

- Never write into `Report Examples/` (it lives outside this repo, on
  Spenser's Mac, at `../RRF/Report Examples/`). Never copy client material
  into this repo.
- Never move, print, or log a key.
- Never create a markdown file, doc, or note that your plan does not name.
  Text for Spenser goes in the chat.
- No em dashes in anything: code comments, docs, UI copy. Hyphens instead.
- Python 3.9 compatible: no `int | None` unions, no `match`. Nobody has
  checked what is on Mark's Windows machine.
- Work on the slice branch your plan names. Commits there are recovery
  checkpoints, allowed because the plan was approved. Nothing is pushed,
  merged, or treated as accepted without Spenser's yes.
- Phase plans are executed on Sonnet or Opus. Never Haiku (Spenser's call,
  2026-08-15).

## Decisions on record (2026-08-15, Spenser, in chat)

These are decisions, not measured facts. They are recorded here so no
session relitigates them; they are not verifiable from disk and do not need
to be.

- **The full appraisal comes first** because it exercises the most
  machinery. The other shapes are different compositions, not subsets: the
  short form combines and omits sections rather than trimming them. Each
  shape's composition comes from the engagement matrix and its recipe,
  never from cutting down the full report. Mark's own use will steer the
  order after handoff.
- **Three classes of file, three rules.** Client source documents and the
  workbook are never touched: the app reads them and nothing more. App-owned
  notes (job-brief.md, photo-manifest.json, the settings and key files) are
  the app's own records and it may rewrite them. Generated outputs always
  get fresh names and never overwrite anything, including earlier outputs.
  The old entry-solve workbook writer stays a dev-side tool.
- **The report must feel exactly like Mark's current reports.** Grids and
  the final PDF come from driving Mark's own installed Word and Excel. On
  Windows that is COM automation (pywin32). No LibreOffice, no hand-rebuilt
  grids.
- **The model drafts words only, always behind Mark's edit.** Deterministic
  code owns every number, every layout, every check. Model territory:
  captions (live and proven), prose sections from dictation, reading the
  engagement letter, sorting dropped documents. A first version where prose
  sections come out as structured blanks is acceptable.
- **The key is Spenser's for now, Mark's eventually.** A consumer Claude or
  ChatGPT subscription does not give API access; that fact is settled and
  should not be relitigated. The mechanism was undecided when this was
  written. It is decided for the Windows Photo Pilot only, on 2026-08-17:
  Mark enters his own key himself, on the Settings screen, on his machine,
  and no key ships inside the package. Outside the pilot the longer-term
  arrangement is still open.
- **Templates are manufactured per section**: cloned from a donor report,
  stripped of client content, passed by the leak scanner, read by Claude,
  glanced at by Spenser, then committed. `app/templates/Photo.docx` is the
  precedent. One exception is on the way, recorded 2026-08-17: where Mark
  supplies a template he intends to follow, that file governs and the
  section is not manufactured from a donor. Description of Improvements is
  the first.
- **The old system is retired.** Nothing in the locker runs for real work.
  It is a read-only quarry (paths below).
- **Spenser is the only user until handoff.** Mark receives one handoff of
  many working capabilities, not a drip. Working line for the handoff bundle:
  everything through Phase 3. Packaging for Windows is a final phase, not an
  early one. One bounded exception was approved on 2026-08-17: the Windows
  Photo Pilot below reaches Mark before that bundle. It is a proof on his
  own machine, not the handoff. It does not move the handoff line, it does
  not stand in for the Phase 1 Windows Office proof, and it is not Phase 5
  packaging.
- **Setup on Mark's machine is screen share only.** Assume nobody is at his
  keyboard. Everything he touches must be one action.
- **The Windows delivery spine is proven inside Phase 1, before Phase 2
  multiplies Office-dependent sections.** The Office bridge is two thin
  backends behind one interface: a Mac backend adapted from the locker's
  AppleScript scripts so Spenser tests real grids and PDFs locally, and a
  Windows backend (COM). Phase 1 is not complete until, on Windows (a VM on
  the Mac is acceptable), the app launches from the intended embedded
  Python package, reads one workbook without changing it, renders one real
  Excel grid, places it into one Word file, and produces one PDF through
  installed Office. That is an early delivery-spine proof, not final
  packaging. Unrelated Mac work may continue alongside it.
- **Commits on a slice branch are recovery checkpoints**, allowed once
  Spenser has approved the slice's plan. Nothing is pushed, opened as a pull
  request, merged, treated as accepted, or delivered without his yes.
  Approved 2026-08-15; the matching HOW-WE-WORK.md wording is in place.
- **The Settings screen may show the key's last four characters**, and only
  there, so Mark can tell one key from another. No other key material ever
  reaches the browser, a log, an error, or any endpoint. Approved
  2026-08-15; the matching HOW-WE-WORK.md wording is in place.
- **Synthetic files prove mechanics, never Mark's world.** Valid synthetic
  files and temporary folders may test narrow mechanics: parsing, error
  handling, naming, confinement, non-overwrite behavior. They prove only
  that mechanic. Claims about Mark's real folders, documents, layouts,
  reports, or workflow require the real corpus. Approved 2026-08-15; the
  matching HOW-WE-WORK.md wording is in place.

## Decisions on record (2026-08-17, Spenser, in chat)

Four more decisions, recorded the same way as the ones above. Where one of
them changes something written on 2026-08-15, the older bullet has been
amended in place, so this file holds one answer and never two.

- **Mark receives an early Windows Photo Pilot, before the handoff bundle.**
  This is the named exception to "one handoff, not a drip", and it is
  bounded. The pilot exists to prove five things on Mark's real Windows
  computer: that the app installs, that it starts, that he can select a job
  folder, that he can set up AI captioning behind the guards below, and that
  it produces Subject Photograph pages. It does not replace the Phase 1
  Windows Office proof. It does not replace the later complete handoff of
  everything through Phase 3. It does not replace Phase 5 final packaging.
  Nothing outside the five things named here is in it.

- **AI captioning is in the pilot, guarded.** The guards are the product,
  not decoration, and they hold together:
  - Mark enters the API key himself, locally, on the Settings screen.
  - No API key ships inside the package.
  - Only whether a key is available, and the key's final four characters,
    reach Settings. That is the 2026-08-15 last-four decision, unchanged.
  - AI runs only after an explicit action by Mark. Nothing captions on open.
  - The screen states how many photos will be sent before he acts.
  - Captions are previewed before anything is built.
  - Request size, retries, and spending are bounded.
  - Captions typed by hand always remain available.
  - AI receives only the selected photos and the approved job context.
  - AI receives no general filesystem access.
  - AI cannot move, rename, edit, or delete a source file.

  This is an approved product direction. It is not authorization to build it
  in any session that has not been handed that work.

- **The photo output is named `City_Address Photos (Complete).docx`.** City
  and address come from confirmed job information, and neither is ever
  guessed. The confirmed values are converted into a Windows-safe filename.
  An existing output is never overwritten: a name already in use produces a
  newly numbered copy instead. That is the three-classes-of-file rule above
  applied to this one output, not a new rule. Not implemented yet, and not
  by the session that recorded it.

- **A newer Description of Improvements template is coming from Mark**, and
  he intends to follow it from here on. Once received, that template is the
  governing source of truth for that section's structure, wording, order,
  fields, and formatting. The file he sends is preserved unchanged.
  Historical delivered reports remain supporting evidence for data
  variations and edge cases, and a historical majority pattern may not
  overrule the new template. This is the one place where measuring the
  corpus yields to a stated instruction from Mark, and it yields for this
  section only. No Description of Improvements implementation plan is
  approved until the actual template has been received and inspected.

## Decisions on record (2026-08-25, Spenser, in chat)

Made after Mark's first real session on his own Windows PC, which found almost
no photographs in any of his jobs. Recorded here because the plan that carried
out the work has been deleted, and these outlive it.

- **The app never reads a folder name for meaning, and asks Mark instead.**
  Measured across eleven real jobs on 2026-08-25: every one keeps each shoot
  twice, full size and shrunk by hand, and the folder names are `Original`,
  `Raw pics_`, `Minimized`, `full size`, `Building`, `Used`, `Reduced`,
  `3525`/`3575` and `Report Photos_`. Nine conventions across eleven jobs, and
  a new helper in Mark's office has just added a tenth. Any rule written
  against those names breaks the next time somebody in that office invents a
  folder. So when a job keeps photographs in more than one place the app shows
  him the folders his own office made, with a photograph and a count from each,
  and he picks one. `Z`, `Do Not Use`, `Used` and `All report photos used` are
  read as plain text and nothing else.

- **The office's hand-shrinking is redundant and costs quality.** Measured on
  the Maquoketa job, 2026-08-25. His helper resizes every photograph to a
  quarter, 4032 x 3024 down to 1008 x 756. The app already caps at 1,600
  pixels and never enlarges, so from the raw file it embeds 1600 x 1200, which
  is 400 dots per inch at four inches wide against 252 from the shrunk copy.
  Once shrunk the quality cannot be recovered. Worse, resizing strips the EXIF,
  which destroys the capture order, which is why the helper then numbers every
  file by hand. Pointed at the raw folder the app reproduced his numbering
  exactly, from capture times, except one pair he had deliberately swapped.
  **The case for asking the office to stop is these numbers.** Sixteen raw
  photographs are 53.2 MB and produce a 3.3 MB document.

- **The right-hand side of the job screen is not the report. It is what
  generates the report.** The report is the Word file, and once he has built it
  nothing in the app reaches into it. He can take a photograph out of the
  staging and build again; he cannot take one out of a document he has already
  made. The heading `The report` stays, because he reads it as the report he is
  making. `Cut from report` does not, and is now `Take out`.

- **The app refuses a claim it cannot act on, and says why.** Marking a signed
  engagement letter a subject photograph used to be recorded, shown back as
  "confirmed by you", and acted on in no way at all. It now answers "That is a
  PDF. Only photographs go on the photo pages." and writes nothing. Only
  `Subject photograph` is ever refused, because it is the only label that
  decides what gets built. What a file is in every other sense is Mark's to
  say.

- **One section, one number.** The job screen counted every image in the Photos
  tree while the Photos screen counted the report, so one section showed 33 on
  one screen and 16 on the next. The job screen now counts what would build.

- **Bulk classify, built 2026-08-25.** He opens a folder, clicks
  `Bulk classify`, ticks what he wants or `Select all`, and one label lands on
  all of them in a single write. Nothing appears on a row until he asks, so the
  screen is unchanged the rest of the time. **A batch may half succeed on
  purpose:** 37 files where 4 are documents applies 33 and refuses 4, each with
  its own reason, and the refused ones stay ticked so his next click can give
  them the label they actually deserve. Refusing all 37 because of 4 would
  punish him for the app's own rule. Ticks die when the folder closes, and
  selecting across folders is deliberately not built until he has wanted it
  twice. Measured on Mason City: 50 photographs in one folder, one click,
  where it was 100.

- **The screen refreshes both bands after a classification, not one.** The
  count beside a section depends on classifications now, so refreshing only the
  file list left it stale: 33 photographs classified in and the section still
  reading 17 until the page was reloaded. Found by looking, not by a test.

### Where the work sits, 2026-08-25

Nothing is merged and nothing is pushed. `bulk-classify` is the tip and every
branch below it is already in it. Ask git for the rest rather than trusting a
list written here, which would start lying the first time anything merges:

    git log --oneline --graph --all --decorate

`build/packages/Roy R. Fisher v0.5.3.zip` was cut on 2026-08-26 and carries
everything in this list. `build/Send to Mark/` still holds the older 0.5.1,
which predates every fix and was never sent. 0.5.2 was cut and then deleted the
same day rather than left lying about, because the thumbnail fix below landed
straight after it and two candidates is how the wrong one gets sent.

**0.5.3 has not run on Windows.** Gate D stands: Spenser tests the exact
package himself before Mark sees it.

- **His jobs are on a mapped network drive**, `Z:`, under a path like
  `Z:\...\NARRATIVE 1\Mark's Appraisal`. Learned 2026-08-26. Every filesystem
  question the app asks there is a request to another machine, so the cost of a
  screen is the number of questions it asks and not the work it does. Nothing
  about that is visible on a Mac.

- **The thumbnail route used to search the whole job for every photograph.**
  Measured on Mason City: 57 photographs meant 57 full walks and 6,954 path
  lookups for one screen. A tenth of a second on a local disk, and up to
  thirty-five seconds over his drive. It now reads where the photograph sits
  out of the manifest, which the app already wrote, and falls back to the walk
  only for a photograph the manifest has never seen. 6,954 lookups became 114.
  `test_thumbnails_do_not_rewalk.py` counts the walks rather than timing them,
  because a timing test passes forever on a fast disk and says nothing true
  about his.

- **Path length was ruled out as a cause of the original defect**, using
  evidence from Mark's own session: the folder listing on the left resolved and
  stated every one of those deep files on his machine while the photo screen
  showed one. His longest path is 194 characters below the jobs folder, which
  leaves roughly 15 to 21 spare under the Windows 260 limit. Real, worth
  knowing, not a blocker today.

**A defect in the packaging script was found cutting it, and fixed.** The wheel
cache is shared between builds and grows, and the install list is built by
diffing that directory. Upstream published click 8.5.0 and websockets 17.1
after the cache was last filled on the 19th, so the build handed pip two
versions of each and died on a ResolutionImpossible. The script now keeps the
newest wheel of each distribution and prints what it dropped. It would have
failed this way on any build made after any dependency released, so it was
waiting for whoever cut the next package.

### Carried out of Phase 0, whose plan has been deleted

Two facts from that plan's closeout that live nowhere else. Everything else in
it was either superseded (its test counts, its "nothing has ever run on
Windows") or is already stated in the README.

- **`readiness_scan.REQUIREMENTS` and its command line are in the tree and
  nothing calls them.** Deliberate. The rewritten Task 7 withdrew the row
  mapping that would have used them, and they wait for the later
  information-needs slice. They are not dead code to be tidied away.

- **The pinned requirements are proven to install on the Mac only.** Phase 0
  built a clean virtual environment from `app/server/requirements.txt` and ran
  the suite green from it. That says nothing about any other platform.

### Where updates will be pushed from, 2026-08-27

Cloudflare R2 bucket `rrf-app-updates`, Eastern North America, created
2026-08-27. Public read is on, through R2's development URL:

    https://pub-62e06bebd88c4f8cb46a00672f5057b2.r2.dev

Public because Mark's machine downloads with no login. The package holds no
key and no client material, so what is exposed is the app itself. Spenser's
call, made knowingly.

Cloudflare labels that URL rate limited and not for production, which is a
warning aimed at public websites. One appraiser downloading a package now and
then is nowhere near it. A custom domain is the upgrade if it ever matters.

**Approved 2026-08-27: Mark presses a button in the app and it updates
itself.** Not automatic and not silent, so the pilot's "no automatic updater,
Spenser installs updates" decision is amended rather than ignored. What makes
it survivable already exists: `install_windows.py` keeps the previous version
and only repoints the Desktop icon, so a bad update is undone by running the
old version's install file.

Not built. Nothing in the bucket yet.

### Still owed out of that work

Named here rather than in a plan, because plans are deleted and these are not
done.

- **Suggesting a classification from the filename, for him to confirm.**
  Currently forbidden: nothing infers a label from a name, a rule set in Phase
  0 after "Has deed" was manufactured from a filename and was wrong. Spenser
  reopened it on 2026-08-25 and the corpus supports him. Measured the same day
  across the delivered reports, his own naming carries a type prefix far more
  often than not: `DEED` 10 times, `PLAT` 8, `PHOTO` 7, `SKETCH` and
  `SKETCHES` 7, `FLOOD` 6, `AERIAL` 3, `ZONING MAP` 3. **The distinction that
  makes this safe is proposing against asserting.** A suggestion he confirms is
  not the same thing as a stated fact, and the Phase 0 rule was written against
  stated facts. Not approved, not designed, and it needs its own measurement
  pass over how often a prefix would be wrong before anyone builds it.

- **A layout pass over the job screen and the photo screen.** Spenser's words
  on 2026-08-25: it is all a little confusing. Not specified yet.

- **Taking several photographs out at once.** A job like Maquoketa carries four
  the office marked `Z` for do not use, and they come out one click at a time.
  Bulk classify does not solve this: taking a photograph out of a section is a
  question about the section, and it lives on the right, where there is no
  choosing-several yet.

- **Selecting across more than one folder at once.** Not built on purpose,
  2026-08-25. It is a different feature from choosing several inside one
  folder, and it waits until he has wanted it twice.

## The working rhythm (stops are scheduled, not hoped for)

- **A goal conversation before each change.** Before a slice starts, the goal
  is stated to Spenser in one sentence and he says yes. Routine steps inside
  an agreed plan do not re-ask.
- **A small stop after every screen change.** Spenser clicks through the new
  screen before it merges, against the "a click leads to a step" rule.
- **A large stop at the end of every phase**, fixed agenda, three questions:
  Does it feel like one app, walked front to back as Mark would? Are we
  showing the right things, with nothing promising more than it does and
  nothing built sitting hidden? Are we getting bloated, and what should stay
  parked? The debrief folds back into HOW-WE-WORK.md and this file.
- **First large stop carries one standing item: adopt the design system**
  (`brand/Roy R. Fisher Design System/`). The screens still run the old
  stylesheet with the wrong red. Adopt before Phase 2 multiplies screens.

## The phases

**Phase 0: make what exists true.** Fix the known defects, pin what is
unpinned, make the README stop lying, and fix the readiness panel so it
never silently discards a requirement and never states an unproven claim.
That plan is executed and deleted; what it left behind is under
"Carried out of Phase 0" below. Ran on the Mac.
The readiness task changes the job screen, so this phase carries one goal
conversation, one row-by-row mapping review, and one small screen stop.

**Phase 1: the Office bridge, both sides.** Excel grid to image and docx
to PDF behind one interface with two backends. The Mac backend adapts the
locker's AppleScript scripts (`xlsm_exhibit.py`, `render_pages.py`) so
every later phase has real grids and PDFs on Spenser's Mac. The Windows
backend (COM, pywin32) is proven by the thin acceptance slice named in the
decisions above: launch from embedded Python, read one workbook untouched,
render one grid, place it in one Word file, produce one PDF. Phase 1 is
not complete until that slice passes, and Phase 2's Office-dependent work
does not start before it does. Unrelated Mac work may continue. The Windows
Photo Pilot does not satisfy any part of this proof: photo pages need no
Office at all, so a pilot that works on Mark's PC says nothing about Excel,
Word, or PDF through COM.

**Phase 2: cheap width.** The image-page family (aerial, neighborhood map,
plat map, sketch, comp map) and the four boilerplate sections whose
templates already exist; neither needs Office, so both may start while
Phase 1 finishes. Note the image pages are not free clones of the photo
machinery: maps, rotated exhibits, and stacked pages have their own source
and layout rules in the recipes, measured before built. Then Salient
Facts, the first section that needs the workbook digest and the grid
renderer together; it waits for Phase 1 to complete. Also: replace the
single hardcoded buildable-section string in
`app/web/src/screens/JobHome.jsx` with a real registry, because this phase
is where one section becomes many.

**Phase 3: the approaches.** Cost, Sales, Income. Each approach's
furniture comes from its own recipe and they do not share one structure:
Sales uses per-comparable pages in one variant only and has two other
measured variants; Income uses rent grids, survey exhibits, and operating
statements, with no per-comparable pages at all; Cost has its own ordered
block list. Grids come from the bridge. Template manufacturing at full
speed under the gate above. Longest phase.

**Phase 4: the model's sections.** Prose drafting from dictation into
structured blanks Mark edits. The engagement letter into the intake form.
The one-drop intake. Everything degrades to typed-by-hand when there is no
key, the way captions already do. Do not explode this phase into a plan
until it has a truth-and-authority contract: which extracted fields are
observed facts and which are model suggestions, what requires Mark's
confirmation, what stays blank when extraction is uncertain, whether
sorting displays a category or moves a file, and where app-owned
classifications live without touching Mark's folders.

**Phase 5: the whole report, and handoff.** Assembly, TOC, addenda, the
delivered PDF. The finish test: the app rebuilds one delivered job per
report shape as that shape's sections land, Mason City first, each result
sitting next to its delivered report. One job cannot validate the system;
one job per shape can validate each shape. Then packaging:
one zip with the app, the built interface, and Python's embeddable Windows
distribution, so Mark's whole experience is unzip once, double-click a
shortcut forever. The Windows Photo Pilot ships a bounded early package to
prove installation and startup. Final packaging is still this phase, and the
pilot does not close it.

## The quarry: what the locker gives each phase

The locker is at `../RRF/locker/` relative to this repo, on Spenser's Mac
only. Read-only. Take copies, adapt freely, never write back.

| Locker source | Becomes |
|---|---|
| `shop/system/sections/*.md` (14 recipes) | Per-section build specs and QA checklists, as code and data |
| `shop/data/section-rulebook.md` | The measured standard behind every layout decision, except where Mark supplies a governing template for a section (see 2026-08-17) |
| `shop/data/conventions.md`, `shop/data/reference/boilerplate-texts.md` | App data files, like `app/data/engagement-matrix.md` already is |
| `shop/data/donors/donor-ledger.md` | The map of which delivered report donates each section's furniture |
| `shop/system/scripts/xlsm_digest.py` | The workbook reader. Quarry input, not a drop-in: 180 lines, pure openpyxl, but it hardcodes its sheet list and writes its digest beside the workbook; output ownership moves to the app |
| `shop/system/scripts/clone_section.py` | Clone-and-fill engine. Quarry input, not a drop-in: 661 lines of donor-specific Word surgery to be adapted per section |
| `shop/system/scripts/placeholder_scan.py`, `standards_check.py`, `leak_sweep.py` | App-side checks and the template-manufacturing gate, adapted |
| `shop/system/scripts/xlsm_exhibit.py`, `render_pages.py` | The Mac backend of the bridge adapts these; the Windows backend (COM) is new code |
| `shop/system/scripts/assemble.py` | The binder. Quarry input: 1,052 lines; the core is lxml concatenation, but it leans on staged copies, pypdf, and a renderer for TOC page numbers |
| `shop/data/templates/boilerplate/*.docx` (4 files) | Phase 2 boilerplate sections, tokens and all |
| `testing/grades.md`, TEST21 records | The benchmark: what good looked like, what failed and why |

## Known risks, named once

- **Nothing has ever executed on Windows.** The mitigation is scheduled,
  not hoped for: the Phase 1 acceptance slice proves the delivery spine on
  Windows before Phase 2 builds Office-dependent sections on top of it.
  What remains after that slice is version drift and full packaging, both
  closed in Phase 5. The Windows Photo Pilot lands earlier and takes a
  smaller bite out of this risk: it proves installation, startup, folder
  selection, guarded AI setup, and photo pages on Mark's machine, and
  nothing about Office.
- **Template manufacturing touches client material every time.** The gate is
  mechanical scan, Claude read, Spenser glance. No shortcut.
- **Mark is hard to manage and setup is remote.** Anything that needs two
  steps on his machine is a defect.

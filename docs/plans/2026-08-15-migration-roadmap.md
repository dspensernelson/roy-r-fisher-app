# Migration roadmap: the locker system becomes the app

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
  checked what is on the appraiser's Windows machine.
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
  never from cutting down the full report. The appraiser's own use will steer the
  order after handoff.
- **Three classes of file, three rules.** Client source documents and the
  workbook are never touched: the app reads them and nothing more. App-owned
  notes (job-brief.md, photo-manifest.json, the settings and key files) are
  the app's own records and it may rewrite them. Generated outputs always
  get fresh names and never overwrite anything, including earlier outputs.
  The old entry-solve workbook writer stays a dev-side tool.
- **The report must feel exactly like the appraiser's current reports.** Grids and
  the final PDF come from driving the appraiser's own installed Word and Excel. On
  Windows that is COM automation (pywin32). No LibreOffice, no hand-rebuilt
  grids.
- **The model drafts words only, always behind the appraiser's edit.** Deterministic
  code owns every number, every layout, every check. Model territory:
  captions (live and proven), prose sections from dictation, reading the
  engagement letter, sorting dropped documents. A first version where prose
  sections come out as structured blanks is acceptable.
- **The key is Spenser's for now, the appraiser's eventually.** A consumer Claude or
  ChatGPT subscription does not give API access; that fact is settled and
  should not be relitigated. The mechanism was undecided when this was
  written. It is decided for the Windows Photo Pilot only, on 2026-08-17:
  the appraiser enters his own key himself, on the Settings screen, on his machine,
  and no key ships inside the package. Outside the pilot the longer-term
  arrangement is still open.
- **Templates are manufactured per section**: cloned from a donor report,
  stripped of client content, passed by the leak scanner, read by Claude,
  glanced at by Spenser, then committed. `app/templates/Photo.docx` is the
  precedent. One exception is on the way, recorded 2026-08-17: where the appraiser
  supplies a template he intends to follow, that file governs and the
  section is not manufactured from a donor. Description of Improvements is
  the first.
- **The old system is retired.** Nothing in the locker runs for real work.
  It is a read-only quarry (paths below).
- **Spenser is the only user until handoff.** the appraiser receives one handoff of
  many working capabilities, not a drip. Working line for the handoff bundle:
  everything through Phase 3. Packaging for Windows is a final phase, not an
  early one. One bounded exception was approved on 2026-08-17: the Windows
  Photo Pilot below reaches the appraiser before that bundle. It is a proof on his
  own machine, not the handoff. It does not move the handoff line, it does
  not stand in for the Phase 1 Windows Office proof, and it is not Phase 5
  packaging.
- **Setup on the appraiser's machine is screen share only.** Assume nobody is at his
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
  there, so the appraiser can tell one key from another. No other key material ever
  reaches the browser, a log, an error, or any endpoint. Approved
  2026-08-15; the matching HOW-WE-WORK.md wording is in place.
- **Synthetic files prove mechanics, never the appraiser's world.** Valid synthetic
  files and temporary folders may test narrow mechanics: parsing, error
  handling, naming, confinement, non-overwrite behavior. They prove only
  that mechanic. Claims about the appraiser's real folders, documents, layouts,
  reports, or workflow require the real corpus. Approved 2026-08-15; the
  matching HOW-WE-WORK.md wording is in place.

## Decisions on record (2026-08-17, Spenser, in chat)

Four more decisions, recorded the same way as the ones above. Where one of
them changes something written on 2026-08-15, the older bullet has been
amended in place, so this file holds one answer and never two.

- **The appraiser receives an early Windows Photo Pilot, before the handoff bundle.**
  This is the named exception to "one handoff, not a drip", and it is
  bounded. The pilot exists to prove five things on the appraiser's real Windows
  computer: that the app installs, that it starts, that he can select a job
  folder, that he can set up AI captioning behind the guards below, and that
  it produces Subject Photograph pages. It does not replace the Phase 1
  Windows Office proof. It does not replace the later complete handoff of
  everything through Phase 3. It does not replace Phase 5 final packaging.
  Nothing outside the five things named here is in it.

- **AI captioning is in the pilot, guarded.** The guards are the product,
  not decoration, and they hold together:
  - the appraiser enters the API key himself, locally, on the Settings screen.
  - No API key ships inside the package.
  - Only whether a key is available, and the key's final four characters,
    reach Settings. That is the 2026-08-15 last-four decision, unchanged.
  - AI runs only after an explicit action by the appraiser. Nothing captions on open.
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

- **A newer Description of Improvements template is coming from the appraiser**, and
  he intends to follow it from here on. Once received, that template is the
  governing source of truth for that section's structure, wording, order,
  fields, and formatting. The file he sends is preserved unchanged.
  Historical delivered reports remain supporting evidence for data
  variations and edge cases, and a historical majority pattern may not
  overrule the new template. This is the one place where measuring the
  corpus yields to a stated instruction from the appraiser, and it yields for this
  section only. No Description of Improvements implementation plan is
  approved until the actual template has been received and inspected.

## The working rhythm (stops are scheduled, not hoped for)

- **A goal conversation before each change.** Before a slice starts, the goal
  is stated to Spenser in one sentence and he says yes. Routine steps inside
  an agreed plan do not re-ask.
- **A small stop after every screen change.** Spenser clicks through the new
  screen before it merges, against the "a click leads to a step" rule.
- **A large stop at the end of every phase**, fixed agenda, three questions:
  Does it feel like one app, walked front to back as the appraiser would? Are we
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
Plan exists: `2026-08-15-phase-0-truth-and-defects.md`. Runs on the Mac.
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
Office at all, so a pilot that works on the appraiser's PC says nothing about Excel,
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
structured blanks the appraiser edits. The engagement letter into the intake form.
The one-drop intake. Everything degrades to typed-by-hand when there is no
key, the way captions already do. Do not explode this phase into a plan
until it has a truth-and-authority contract: which extracted fields are
observed facts and which are model suggestions, what requires the appraiser's
confirmation, what stays blank when extraction is uncertain, whether
sorting displays a category or moves a file, and where app-owned
classifications live without touching the appraiser's folders.

**Phase 5: the whole report, and handoff.** Assembly, TOC, addenda, the
delivered PDF. The finish test: the app rebuilds one delivered job per
report shape as that shape's sections land, Mason City first, each result
sitting next to its delivered report. One job cannot validate the system;
one job per shape can validate each shape. Then packaging:
one zip with the app, the built interface, and Python's embeddable Windows
distribution, so the appraiser's whole experience is unzip once, double-click a
shortcut forever. The Windows Photo Pilot ships a bounded early package to
prove installation and startup. Final packaging is still this phase, and the
pilot does not close it.

## The quarry: what the locker gives each phase

The locker is at `../RRF/locker/` relative to this repo, on Spenser's Mac
only. Read-only. Take copies, adapt freely, never write back.

| Locker source | Becomes |
|---|---|
| `shop/system/sections/*.md` (14 recipes) | Per-section build specs and QA checklists, as code and data |
| `shop/data/section-rulebook.md` | The measured standard behind every layout decision, except where the appraiser supplies a governing template for a section (see 2026-08-17) |
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
  selection, guarded AI setup, and photo pages on the appraiser's machine, and
  nothing about Office.
- **Template manufacturing touches client material every time.** The gate is
  mechanical scan, Claude read, Spenser glance. No shortcut.
- **The appraiser is hard to manage and setup is remote.** Anything that needs two
  steps on his machine is a defect.

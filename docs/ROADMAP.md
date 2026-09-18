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

- **The Description of Improvements template is approved.** Amended in place
  2026-09-16 by Spenser. This bullet first said a newer template was coming
  from Mark, and that no implementation plan was approved until that file
  arrived and was inspected. **That gate is struck.** No file came from Mark.
  We authored the template ourselves from the Blaul Lofts report, and Spenser
  approved it. `app/templates/Improvements.docx` on the `improvements-section`
  branch is the governing source of truth for that section's structure,
  wording, order, fields, and formatting. Historical delivered reports remain
  supporting evidence for data variations and edge cases, and a historical
  majority pattern may not overrule it. The layout is recorded in the plan
  document on that branch: Blaul Lofts, plus the two blocks Blaul leaves out,
  whose labels come from the 215 E 37th report.

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

**Built 2026-08-28** on the `in-app-update` branch. Nothing is in the bucket
yet, nothing is packaged, and nothing has run on Windows. What follows is the
durable part of the plan that carried it out, which has been deleted.

### How the update works, and why it is shaped that way, 2026-08-28

**Windows will not let a running program replace its own files.** That single
fact shapes everything else: the app cannot install an update over itself, so
it fetches, checks, hands off to a separate process, and exits.

The order, and the order is the safety property:

1. The app reads `latest.json` from the bucket once when it starts, in the
   background. Nothing is shown unless a newer version is actually offered.
2. Mark clicks. He is told which version, how big, and what will happen.
3. The zip downloads into `~/.rrf-app-download/`.
4. It is checked against the `.sha256` published beside it.
5. It is unpacked and checked with `packaging.verify`, the same check the
   launcher runs on every start.
6. Only now does anything out of the bucket execute: the **new** package's
   `python.exe` running the **new** package's `app/update_apply.py`, in its own
   console window.
7. The app clears its `runtime.json` and exits.
8. The child waits on `install_windows.something_running`, which is the exact
   condition the install refuses on, then calls `install_windows.install()`.
9. The child starts the new version and exits.

**The child runs the new package's Python, not the old one's.** Once the
handoff starts, nothing in the old version folder is held open, which is what
leaves `install_windows.py` free to copy over it and to prune it.

**`hand_off` refuses any package not recorded as having passed both checks in
this run.** That record is written inside `prepare`, where no caller can reach
it. An order that depends on every caller remembering the order is not a safety
property, so it is not implemented as one.

**Rollback is the one that already existed and was not touched.**
`install_windows.py` keeps the previous version and repoints one Desktop
shortcut. No second mechanism was built.

### What the checking does and does not do, 2026-08-28

It catches a damaged or incomplete download: an interrupted transfer, a
truncated file, a flipped byte, a package that did not unzip whole.

Without code signing it does **not** prove who built the package, and it does
**not** protect against anybody able to rewrite both the zip in the bucket and
the `.sha256` beside it. Whoever can replace one can replace the other. This is
an integrity check against accident, not a security control against an
adversary. It is the same limit `packaging.py` already states about the
manifest, and it is said in those words in the code and on the screen where
Mark decides.

The bucket is public and the app only ever fetches from it. Nothing about Mark,
his jobs, or his machine leaves the computer. A test watches the requests
rather than reading the source, because a body added later would still look
like a GET in the source and be a POST on the wire.

### Decisions on record (2026-08-28, Spenser, in chat)

- **`latest.json` is what the app reads to learn a version exists.** The
  packaging script writes it, holding the version, the zip's filename and its
  size. The hash is deliberately not in it: it stays in the `.sha256` sidecar,
  written from the archive itself, so there is one value of record rather than
  two that can disagree. Spenser uploads three files and authors none of their
  contents, so a mistyped version or hash stops being possible. The script
  prints the three names and says to upload `latest.json` last, because until
  it changes nobody is offered the version.
- **The notice sits in the masthead beside the version, on every screen.** It
  is the same chip, so nothing moves when one becomes the other.
- **A real progress bar in megabytes**, a sentence per stage, and a Cancel
  during the download. His jobs are on a network drive and a bar that says
  nothing looks like a hang.
- **At the end the app closes itself and the new version opens on its own.**
  One action from him, which is the rule for his machine.
- **The app looks once at startup, in the background, silently.** No internet
  and a bucket that is down look exactly like no update, because neither is
  something he can act on. `Check now` on Settings answers either way, because
  there he asked.

### Measured, 2026-08-28

- The real v0.5.3 package is 53.3 MB zipped and 116.8 MB unpacked, a ratio of
  2.19. `install_windows.py` then copies it again, so one update needs about
  287 MB on disk at once. The free-space floor is written as that arithmetic
  with the measurement beside it, not as a number somebody picked.
- The scratch folder is `~/.rrf-app-download/` and deliberately not inside the
  install home: `install_windows.version_folders` reads every folder there as a
  version and `_prune` deletes the oldest, so a scratch folder there would
  eventually be deleted as one. It is cleared at the start of every attempt,
  never at the end, because the process that finishes an update is running out
  of it and cannot delete the ground it stands on. So up to about 170 MB sits
  there between updates.
- `tools/photo_source.py` could not find `Report Examples` from a git worktree,
  which errored fifty packaging tests on a machine with the corpus sitting
  right there. `app/tests/conftest.py` hit the same thing when the repository
  was split out and fixed it by looking in more than one place; this module
  never got that fix. It has it now, plus an `RRF_PHOTO_SOURCE` override.
- `busy.wait_until_idle` was added because the update ends by exiting the
  process. Every app-owned file is written to a temporary file and moved into
  place, so an interruption cannot corrupt one. It can still lose one, and
  losing a caption run he has just approved is a bad way to find that out.

### What is proven, and what is not, 2026-08-28

Proven on the Mac: reading and validating the bucket, refusing every shape of
nonsense it can serve, the download, the hash check, the archive safety check,
the manifest check, the guard that stops anything unchecked being run, the
command line the handoff builds, the child's waiting and refusing and
installing, that a spawned child outlives its parent, the routes, and the
screens.

**Not proven, and all of it needs Windows:** that `CREATE_NEW_CONSOLE` gives
the child a readable window, that the child survives the parent's console
closing, that a real download from R2 through Mark's network completes, that
SmartScreen does not object to a bundled `python.exe` spawning another one, and
that the whole thing works end to end on his machine. Gate D still stands:
Spenser runs the exact package himself before Mark sees it.


### The delivery fail-safe, 2026-09-03

**A version that installs and then will not start is a failed update.** Decided
by Spenser on 2026-09-03, after 0.6.5 did exactly that.

**What went wrong.** 0.6.5 installed cleanly, reported that the update had
worked, and could not start. `uvicorn` reads its logging settings from the
console, `pythonw.exe` gives it none, and the app raised before it ever served.
Nothing checked. `update_apply.py` said in its own docstring that failing to
start was not a failed update, because the Desktop icon already pointed at the
new version. That held until a version could not run at all.

**Three layers. The third is the one that would have stopped it.**

1. **The update watches the new version answer.** `update_apply.apply` waits up
   to 120 seconds for `install_windows.something_running` to report the version
   it just installed. Not something answering, that version answering: the old
   one coming back up answers too, and that is not this one starting. If it
   never does, the update reports a failure and holds the window open.

2. **The way back goes on the Desktop, and only while it is needed.**
   `Start previous version.bat` has been written into
   `%LOCALAPPDATA%\Roy R. Fisher\` by every install since the installer
   existed, and on 2026-09-03 nobody knew. It stays where it is. What is new is
   `install_windows.put_way_back_on_desktop`, which puts a
   `Go back to the last version.bat` on the Desktop at the one moment it is
   worth something, and `take_way_back_off_desktop`, which takes it away as
   soon as a version does start. Deliberately not permanent: Spenser asked on
   2026-09-03 for one icon that starts the app, and a second icon sitting there
   in normal use is that same confusion again.

3. **The bucket is only updated after the virtual machine has run that
   version.** A rule, not code. 0.6.5 was published to Cloudflare having never
   started on any Windows machine, so the first person to run it was the person
   it stranded. The local server at `http://192.168.64.1:8088/` exists so a
   version can reach the virtual machine without reaching the bucket, and it
   was not used. Nothing enforces this and nothing can. It is written here so
   it does not live in one person's memory.

**What layer 1 cannot see.** It knows the app answered `/api/version` as the
right version. It knows nothing about whether the photo screen works. That is
what `docs/CHECKS.md` is for. The two do different jobs and neither replaces
the other.

### The Office bridge works on Windows, 2026-09-04

**The Phase 1 gate is met for the mechanism.** The app drove Excel and Word on
the Windows virtual machine, through `pywin32`, and produced a grid picture and
a PDF. Nothing had ever done this on Windows before.

**What ran, in order.** Read a range with no Excel involved. Excel copied it as
a picture. That went into a Word file. Word made a PDF. Spenser ran it; the
files came back to the Mac and were looked at, not taken on trust.

**Three things this found that no test could have.**

1. **`pywin32` loads.** This was the real risk. The package installs libraries
   with pip's `--target`, which runs no setup steps, so `pywin32.pth` is copied
   in and never read. `office_win._wake_pywin32` does that work by hand, and
   the run reported "through pywin32", so it worked. The PowerShell fallback
   was not needed and stays for the machine where it is.

2. **The first Windows grid was too small to use.** 3.7 KB against the Mac's
   30.6 KB for the same grid, because Excel exports a chart at screen
   resolution and offers no way to ask for more. Fixed by making the chart
   larger and stretching the copied picture to fill it, which costs no
   sharpness because the copy is a drawing rather than dots. 21.9 KB after.

3. **"Everything worked" and "this is good enough" are different questions.**
   The check tool reported success on the soft picture, correctly: every step
   finished and every file appeared. Judging the picture needs a person, which
   is why `docs/CHECKS.md` Check 14 asks somebody to open the PDF and look.

**Then one of Mark's real grids ran on Windows too**, the Utica Ridge
assessment block, twelve columns wide. It came out with his grey banner, his
wrapped headings, currency, percentages and row rules, and nothing clipped. The
workbook was not changed.

**That run found a fourth thing, and it is the best argument in this whole
file for the fallback.** The sharpness fix above broke `pywin32`: it asked for
the pasted picture by calling the collection rather than by naming `Item`, and
it did not wait for the clipboard. Excel answered "the index into the specified
collection is out of bounds". PowerShell did the work instead and the grid came
out correct, so the run reported success and nobody would have known.

Two things caught it. The log line `_note` writes when the first way fails, and
the `office.ps1` the fallback leaves behind. **Spenser asked for that log after
being talked out of it once.** Without it this would have shipped as a machine
that quietly pays for a failed attempt on every grid.

Fixed by naming `Item` and by looking up to ten times over three seconds. Proven
on 2026-09-07: the real grid ran again, no `office.ps1` was left, so `pywin32`
did it.
### The colour law, 2026-09-08

**Colour answers one question: can he take it back?** Decided by Spenser on
2026-09-08. Not how important a control is. Position and size already say that.

**Why it was needed.** Eighteen buttons in the app were brand red, including
`Cancel` and `Not now`. The loudest thing on several screens was the way out.
Settings carried five red buttons and no way to tell which one mattered.
Counted on 2026-09-08, not estimated.

**The five states.**

| Looks like | Means |
|---|---|
| Filled red | Cannot be undone, and it is why he came to this screen. **One per screen at most.** |
| Filled blue | It does work for him, and he can undo it or ignore it |
| Plain button, red text (`.button.final`) | Cannot be undone, but it is not why he came |
| Blue text, no box (`.linky`) | Moves him, shows him, or backs him out. Nothing changes |
| Grey, still labelled, with a reason (`.is-off`) | Cannot be used yet. Never hidden, never silent |

**The whole app carries three filled red buttons**: `Build photo pages`,
`Make the job`, `Update now`. Each one writes something into a folder Mark
keeps, or replaces the program.

**Why `Generate captions` is blue and `Build photo pages` is red**, which is
the pair that made Spenser ask for a rule. Generating spends money, which feels
like the serious one. Money is not the axis. Captions are a draft he can
retype, clear, or run again. Building puts a Word document in the client's
folder. Only one of those is stuck.

**Red also draws things that are not controls**: the letterhead band, the line
on top of a card, the rule on the live row. Those are identity and selection.
**A red rule is never a control. A red fill always is.** The shape tells them
apart, so the two uses of red do not fight.

**Applied to the two switches, 2026-09-14.** `Bands On/Off` and `Per page
Three/Six` filled their chosen half with brand red, so the loudest thing on
the photographs screen was a toggle, and both halves are completely undoable.
The chosen half is now raised and white out of a sunk track, in full-strength
ink, which is how the style window's segmented control has always shown
selection. No new colour was invented and `Build photo pages` keeps the
screen's one red fill. Held by a test, because a rule nobody is reminded of
lasts until the first busy session.

### The photographs screen, rebuilt to the theory, 2026-09-15

**Spenser approved the whole screen as a mockup that night**, after eight
rounds of changes he asked for one at a time. It is the first screen built
against the five-kinds theory rather than against the last screenshot he sent,
and it is what the theory is for.

**What he sees now.** The screen is titled with the name of the document the
build will write, greyed to `file name here.docx` when the name cannot be
worked out yet, with the way to correct it beside it. Under the title the two
numbers that describe that file, and the page count is exact: sixty
photographs at three to a page is twenty pages, because the app knows the
layout. Under that one quiet line, which is where every message that is only
telling him something now lands. Upper right, one widget holding everything he
can do and the two settings that shape what comes out.

**Two homes for a message, and no third.** Anything that needs his answer is a
window over the screen. Everything else is that one line. It had eleven boxes
that could stack above his photographs, which is what he asked about on
2026-09-04, and the boxes are gone: the run, the cost, the finished document,
the review count, the bands still waiting, the folder a photograph came from.
What blocks a button is said by that button when he hovers it, which took the
three grey paragraphs about a missing key off the screen entirely.

**Nothing moves.** The header has a 76px floor and grows to the widget, the
widget is pinned at 360 by 110, and the quiet line keeps its 20px whether or not
it has anything to say. Because the widget's height is pinned, the header is
110px in every state. Amended in place 2026-09-17, twice. This said the widget
was 500 by 76, which stopped being true when commit 2a020a4 built the widget he
approved on 2026-09-16; the 500 and the 516 measured below are how the widget
was sized before that design replaced them. It also said the header was a fixed
76px. That pin is what let the first row of photographs cover the bottom of the
110px widget, and commit e8b07de made it a floor, as the approved design at
`docs/design/photos-widget.html` has it (`app/web/src/brand.css`, `.screen-head`).
The widget's width was measured rather than guessed: 473px for its widest
ordinary state, 480 with a three-digit count, which is the 131-photograph job.
A test holds the DOM shape across five states, because a layout that has moved
once will move again the next time a button is added.

**One window for the money.** Generating captions used to open a style window
and then a second window on top of it quoting the same figure twice. It is one
window now: the count in the title, the figure in the corner, the two styles,
his own photographs captioned in the lit style, and the button that spends it.

**Three lines deleted on his instruction**: "Drag a photo to reorder it",
"Build waits until you have read them all", and "Captions are saved as each
request finishes." A hint lives on the thing, not as a sentence.

**Two controls stopped looking like each other.** Bands is on or off, so it is
a switch. Photographs to a page is a value, so it is a track of values. The
colour law of 2026-09-08 still reads off both and neither carries a red fill.

Shipped as 0.7.2.

### Settings in two columns, 2026-09-15

**Click 11 of the walk of 2026-09-04, built eleven days late.** His words then:
*"We have boxes that are left, and there's too much empty space on the right...
There are 4: 1, 2, 3, 4. I think this needs to be reconfigured."* His words on
2026-09-15, looking at the shipped screen: *"why does the setting screen still
look like 5 panesl down instead of 1 | 2 / 3 | 4 / 5 | 6"*. It had been
recorded as a complaint about red buttons and closed by the colour rule, which
is written up in `docs/THE-WALK-2026-09-04.md`.

**Two columns now, and the order is an argument.** Left: the key, where the
jobs live, what the app has done. Right: the version, closing the app. The key
card went from third to first because it is the only card on the screen that
changes what the app can do; the two it used to sit under are set once and
never touched again. Below 900px there is one column, in that same order.

**Two paragraphs folded away**, which is *"Things should be hidden more too."*
Where the key file is kept, and what the app writes into its log. Both are
reassurance, both were read on every visit forever, and both are one click
away behind a link that names the answer.

**A line of code came off the screen.** *"This is set by RRF_JOBS_HOME on this
computer, which overrides the saved choice"* is now *"This computer is set to
use this folder. Changing it here will not stick."*

**`.linky` carries `margin-left: auto`**, so every link on a settings card was
flung to the card's far edge, away from the words it belonged to, and `Change
jobs folder` and `Start setup over` sat at opposite ends of one row. Turned off
inside the card, the same way the title row and the photographs widget already
turn it off.

### The photographs widget, 2026-09-15

**Spenser on Windows:** *"Look how tight that little icon in the upper right
is."* He was right, and the measurement says why. The panel's contents sat 9px
from its walls, and 9px was all the room it had: the top row needs 440.8px of
controls in Helvetica and 451.1 in Tahoma, the widest Windows face this
stylesheet can fall back to. At 500px wide the panel had about 7px spare on his
machine. It looked full because it was full.

**Walls 14px, gaps 9 and 8, width pinned at 516.** The height stays 76px, which
is what stops the screen bouncing. (Amended 2026-09-17: true on 2026-09-15. The
widget is now pinned at 360 by 110, and the header grows to it; see above.) Measured in a browser against this
stylesheet, widest state: `Generate captions` carrying a three-digit count,
which is the 131-photograph job.

**What the photographs gained: nothing, and that is the finding.** Measured at
a 1309px window before and after, the grid is the same five columns of 216px.
It spans the whole page and the panel never shared a row with it; the panel's
right edge already sits exactly on the photographs' right edge, which is the
page's right margin. The only thing a narrower panel would give back is room on
the document's title line, and that line already has slack. **The panel cannot
be made narrower without taking a control out of its top row.** The approved
design at `docs/design/photos-screen.html` has three there and pins 386px; the
app has four, because `Clear captions` was added after the design was approved.
Taking it out is Spenser's decision, not a builder's.

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

- **Putting the way back somewhere Mark can find it. Done 2026-09-03**, and
  written up above under the delivery fail-safe. Noticed 2026-08-28 while
  building the update button and left alone then. It cost Spenser an evening on
  2026-09-03, when the way back was on his own machine the whole time and
  neither of us thought of it.

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

## Decisions on record (2026-09-07, Spenser, in chat)

Made while building the photo page that holds six, F4. Recorded here because
the plan that carried out the work has been deleted, and these outlive it. The
last two were made the same day about photo bands.

- **A value that is copied is a value that will lie, and a second case is what
  makes it lie.** `PHOTOS_PER_TABLE = 3` sat in the engine and the browser had
  already written its own `Math.ceil(length / 3)` beside it. Both were correct
  for as long as there was one layout. The moment a second one existed the copy
  was wrong and nothing could have caught it, because nothing compared them.
  This is the third time the same fault has been paid for: the brand red written
  out instead of pointed at, and the corpus path copied into four files. The
  number now lives in one `Layout` object and every count reads it.

- **Declare a row the height it will actually be.** Mark's three-up template
  declares rows 2.926 inches tall and the app puts a 3.00 inch photograph in
  them, so every row grows past its own declared height, a full page ends up a
  fifth of an inch too tall, and the empty paragraph after the last table lands
  on a page of its own. `_drop_trailing_blank_paragraphs` exists to clean up
  after that. Six-up declares 2.60 inches for a 2.40 inch photograph and needs
  nothing cleaned up after it. The cheapest fix for a layout defect is usually
  in the template, not the code that fills it.

- **A test that fails by design is not a test.** A six-up page whose captions
  fill three over-long rows overflows, and the first plan said to write a test
  asserting it does not. That test could only ever fail. What shipped instead
  records where the edge is and passes: the page carries two over-long rows and
  no more, proved alongside a separate test that builds the worst page Mark's
  own two hundred captions can produce and shows it fits with the full 0.40 inch
  of slack spare. **What the app should do when a job crosses that edge is not
  decided, and shrinking the photographs to dodge it is not the answer.**

- **Photo bands start fresh on every job.** Spenser, 2026-09-07, while
  approving the switch that turns bands on. Carried here on 2026-09-17 from
  `docs/plans/2026-09-07-the-bands-switch.md`, which deletes itself. A new job
  starts with A, B and C only. The app does not remember Warehouse from the
  last job. Wanting that is a want, and it needs a store outside the job
  folder, so it is not built.

- **A band's letter is never chosen on screen.** Same day, same plan, carried
  here for the same reason. `PUT /api/jobs/{name}/bands` gives a letter to any
  band arriving without one, and refuses a letter the job does not already
  have. That is what keeps a rename from silently repointing every photograph
  in the band.

- **The self-immolation rule only bites inside `docs/plans/`.**
  `app/tests/test_plans_delete_themselves.py` reads that one folder and only
  sees files written with task checkboxes. A design document written anywhere
  else, however carefully it says it should be deleted, will quietly outlive
  the work. A spec for this feature was nearly filed in `docs/superpowers/`,
  where nothing would ever have noticed it again. Work documents go in
  `docs/plans/`, with checkboxes, or the rule does not apply to them.

- **Measure the corpus, not the example in front of you.** The six-up caption
  column was sized against two hundred distinct captions read out of every
  report Mark has delivered, not against the page that happened to be open. At
  the three-up width 73% of what he writes wraps to two lines or more; at the
  six-up width two thirds of it fits on one. A page sized against one short
  caption would have looked right and overflowed in the field.

## Decisions on record (2026-09-14, Spenser, in chat)

Made after the Windows machine refused to start 0.7.0 and told Mark to close a
window that has not existed since 0.6.5.

- **A refusal with nothing attempted is not a refusal, it is a dead end.** The
  app may not say no until it has tried the thing it is asking him to do. It
  now asks the running copy to stop, over the same `Close the app` route the
  Settings screen uses, waits for it to really stop answering, and only then
  says anything. When it does say something, it says what it already tried,
  offers a restart, and names Task Manager on the last line and nowhere else.

- **A version number cannot tell one build from another.** Four builds on
  2026-09-14 all called themselves 0.7.0, so a newly unpacked copy handed Mark
  a two-hour-old one and nothing could have noticed. `/api/version` answers
  with a string that two different builds can share, so "it is already running"
  is not a fact the app can observe. Whatever is running is stopped and this
  copy takes over, in both branches. The other half of the answer is procedure:
  **every build that is handed over gets its own number**, and a number that
  has been built once is never built again.

## Decisions on record (2026-09-15, Spenser, in chat)

Made after the same fault was found in the other door. 0.7.1 fixed the
launcher; the installer still refused, with *"Roy R. Fisher 0.7.0 is running.
Close its window, then run this again."* Mark unzips a package and runs the
installer by hand, so nothing ever asks the running copy to close, and there
is no window to close. Spenser: *"We need something that kills it because I
can't actually see that 0.7.0 is running anywhere."*

- **Stop it automatically, in every door.** Somebody who double-clicks the
  installer is trying to use the app, and the app writes every change as it is
  made, so a copy that is stopped loses nothing. The installer now asks the
  running copy to stop over the same `Close the app` route the Settings button
  and the launcher already use, polls until it really stops answering, says
  each step on the console, and only then copies. It refuses only when the copy
  will not go, and that message says what was tried before it asks for
  anything.

- **One message, one place, with the last line as the variable.** The launcher
  sends him back to the Desktop icon and the installer sends him back to the
  installer, so `startup.would_not_stop` takes the next step as an argument
  rather than being written out twice. Copying it would have been the same
  defect this project has already recorded five times.

- **Nothing on his screen is called a window.** Three more messages still named
  one: the launcher's failure report, which reaches him as a message box; the
  update's give-up line; and the packaged README, which told him to leave the
  black window open, to start the app from it, and to photograph it. All fixed,
  and a test now reads the README and refuses the word.

## Decisions on record (2026-09-17, Spenser, in chat)

Made while answering the notes he left on the published checklist. Recorded
here because the checklist lines that asked these questions have come off it.

- **Description of improvements is still the next major area.** He said yes.

- **The 8 September Fable analysis is the plan, as a thought.** It is recorded
  below, under its own heading. Re-run the analysis once description of
  improvements has reached Mark, past beta and testing.

- **When the assessor card and the inspection transcript disagree, the app
  shows both and Mark picks. Neither is filled for him.** Amended in place the
  same day, 2026-09-17, after a measurement overturned the first answer. The
  first answer was that the card fills the field and the transcript shows beside
  it. Across four delivered jobs, twelve fields had both sources speaking and
  disagreeing. Mark followed the card once, the transcript three times, printed
  both four times and followed neither four times. The transcript wins on what a
  thing is made of; the card wins on counts, areas and dates; in eight of twelve
  he did not choose a source at all. Any rule that picks a source is wrong about
  two thirds of the time. Spenser, on seeing it: make sure he is the one
  choosing. On St John Vianney the signed report printed the rectory's roof
  under the church heading, which is the clearest case for showing the quote
  beside every value rather than deciding.
  - **This restores rule 3 of the parked plan**,
    `docs/plans/2026-08-29-description-of-improvements.md` on branch
    `improvements-section`: "The app never settles a disagreement. If the card
    and the transcript differ, show both and let Mark pick."
  - **The parked branch never built that rule.** It kept whichever value the
    model listed first and dropped the other without saying so:
    `app/web/src/screens/ImprovementsScreen.jsx:150-152` on that branch.

- **A, B and C stay in the box. Clicking one filters the photographs to that
  band.** Not built yet. The unbuilt part of the 7 September plan
  `docs/plans/2026-09-07-the-bands-switch.md`, where a click on a band opens a
  step to rename or remove it, is set aside.

- **Who wrote each caption is the next slice.** Recording it is what lets
  written and reviewed be two counts.

- **Two sentences that guessed get new words.** He approved both by looking at
  a rendered before and after. Being built on a branch by another builder; not
  on `working` when this was written.
  - The loading page, after 20 seconds with no answer, says "Roy R. Fisher is
    not answering. Close this tab and double-click the icon."
  - Settings, when Check now cannot reach the update server, says "Could not
    check for a new version." instead of "You are on the newest version."

## The 8 September Fable analysis, recorded 17 September

**Re-run it once description of improvements reaches Mark.** Spenser decided on
2026-09-17 that this analysis is the plan, as a thought, and that it is run
again once description of improvements has reached Mark, past beta and testing.

Written by Claude on 2026-09-08 and never saved to the repository. It lived
only in that session's log. Recorded here on 2026-09-17 with its findings and
its reasoning intact; the wording is tightened in places and nothing it
concluded has been changed. Figures in it, such as the test count and how far
the parked branch had drifted, are as they were on 2026-09-08. On 2026-09-17
the parked branch was 160 commits behind, not 78.

Its list of what should exist once was also nine lines on the checklist until
2026-09-17. They came off in favour of one line: re-run this analysis.

**Three findings from the last round of reading changed the analysis.** The old
system's own operating rules, read in full, are about half compensations for a
runtime that forgets. The two built sections in the app implement the same five
patterns twice with no shared code. And the old system's hard-won rule that
records beat field notes on physical facts is the opposite of what the new
Description of Improvements plan says.

**In one paragraph.** You have a product platform with one section on it. You
are building a report engine whose fourteen sections are six kinds of work over
eight kinds of page content. What connects them is not yet written: a
definition of what a section is, one home for what the app knows about a job,
and a ledger of facts that says where each value came from.

### What you have now

**The old system was a procedure executed by a model.** Strip away the files
and it was this: a model read a written procedure, looped over the state of a
folder, called scripts as tools, and talked to Mark through a scoreboard and
one popup per turn. The filesystem was its database. Markdown files were its
memory. Delivered reports were both its template library and its answer key. A
human was its event loop: nothing happened until someone said so, and every
input arrived as a file drop. Its central idea was that format should be
inherited from delivered work rather than re-derived, and its central
discipline was that numbers come only from the workbook or a document,
judgment is Mark's, and a conflict is flagged, never settled.

Read its operating rules with one question in mind: would this rule exist if
the runtime had memory, a screen, and control of its own files? About half
would not. The scoreboard format, the one-popup rule, the banned words, the
decisions file, the checklist file, the prove-missing rule, the output-folder
hygiene rule, the kit staging and byte audit, the source-trail companion files,
the delete-the-digest dance, the renderer parity rule, and the proctor gates on
tests are all patches for a runtime that forgets, litters, and cannot see. The
other half is domain knowledge, and it is good: the engagement matrix, the
measured rulebook, the map of where every input comes from in the world, the
verbatim citations, the folder guides, the precedence rule for conflicting
sources, the footer-year rule, the rule that candidate values are never picked,
the transmittal value-block variants, and the per-shape gates on thin evidence.

Where it broke is precise. It reached production quality on correctness twice
and never on look. The failures cluster in one place: anything that needs
pixel-exact reproduction. Grid pictures from Excel, exhibit pages bound at the
right spine position, front matter with the logo, approach depth made of dozens
of pasted images. A model orchestrating scripts by rendering pages and looking
at them is a poor renderer. That is not a flaw in the recipes. It is a flaw in
using a model as the runtime.

**The app is a reconciliation loop over Mark's folders, with a product platform
under it.** The app never owns his files. It reads a folder, reconciles what it
sees against its own notes, shows him the difference, and asks one question
inside one action. Its invariants are enforced by code and by 1,413 tests
rather than by instruction: three classes of file, refusals worded as sentences
with a door, no key past the server, a click leads to a step, a spend confirmed
before it happens, a file never overwritten. The model is a component with a
narrow contract. The corpus plays the same role it played for the old grader,
the answer key, but automated and cheap. The platform is real and shared:
atomic state, busy and progress, usage and pricing, the log, packaging,
install, update, settings. The parked Description of Improvements branch reused
pricing, usage, and state without touching them, which is the proof.

Underneath, it is still a photograph application with a job shell around it.
Nearly half the route file is photo logic. The photo module and photo screen
are the two largest files in the tree. The job screen is a folder inventory
with one section name typed into the code. Eight of nine classification labels
act on nothing. The old readiness table sits in the tree unread, which means
the app has lost something the old scoreboard could do: say "waiting on: the
deed" per section.

**The claim that the app has replaced the old system everywhere it has been
built is true only in a narrow sense.** For job setup and photo pages, the app
exceeds the old system in every respect. But the old system could draft
thirteen of fourteen sections and bind them into a report, badly. The app
drafts one section and cannot bind. What the app has replaced is the old
system's runtime and platform: the chat agent, the memory hacks, the human
event loop, the absent delivery. What it has not replaced is the old system's
coverage or its binding, and its knowledge has migrated at the rate of one
section in fourteen. No number has yet flowed through the app, so the old
system's strongest property, every figure traced to the workbook, has no
counterpart in the app at all. The old system is retired. It is not replaced.
It is a quarry that is mostly unquarried.

**What the migration really is.** The proposed framing is right on three axes
and wrong on two.

- **Persistent state:** yes, strongly, though fragmented.
- **Bounded model use:** yes, and narrower than before, with one mechanism the
  old system lacked, quote verification against the source.
- **Reusable rendering:** half. The Office bridge is reusable and proven. The
  Word layer is two parallel implementations.
- **Deterministic services:** the old scripts were already deterministic. What
  actually changed is that the orchestration became deterministic. The model
  was demoted from runtime to component.
- **Sections as data:** not yet, and on this axis the app is behind the old
  system. The old system held its section knowledge as recipes with instance
  counts, a rulebook, a readiness table, and a rubric ledger. The app holds the
  engagement matrix and one layout file consumed by a bespoke module.

Three things the framing misses. The human's role changed from event loop to
operator, which is what forced the hygiene rules into code. The corpus changed
from template library to test oracle. And delivery, absent in the old system,
is a third of the app. So this is a migration of runtime and platform first and
knowledge second, and the knowledge migration has barely begun.

### What you are building

**Fourteen sections are six kinds of work.** Measured over whole delivered
reports, not only the two sections. Every numeric grid in the corpus is a
pasted picture from Excel. The Word tables that exist are the photo pages, the
correlation value box, and front matter. A sales comparison section in the
Utica report is prose blocks, one comparables grid picture, one map picture,
and one table, over about 150 elements. So the page content of every section is
a composition of eight primitives:

| Primitive | Where it appears |
|---|---|
| A picture placed on a page under a running header | Aerial, neighborhood map, plat, sketch, comparable map, traffic map |
| A repeated picture-and-caption cell | Photo pages |
| A labelled field: bold label, tab, value | Description of Improvements, Salient Facts, Site Analysis, Neighborhood, Market Overview sub-heads |
| A grid picture rendered from a workbook range | Assessment grid, building summary, unit mix, sales grid, cost table, income summary, the ESRI market profile |
| Prose with a known provenance: verbatim boilerplate with slots, model text from ticked facts, model text from data, or Mark's own | Every narrative section |
| A sub-block repeated per entity: per building, tenancy, scenario, comparable | Improvements, approaches, scenario reports |
| Page furniture: running header with CONTINUED, page X of Y, copyright year, margins | Every section |
| Binding: order, table of contents, addenda, PDF | The report |

Sections then group by what drives them and who supplies the words, because
that is what decides the screen:

| Kind of work | Sections | Source | Model's part |
|---|---|---|---|
| Image assembly | Aerial, maps, plat, sketch, comparable map; photo pages are the rich case | Files Mark drops or chooses | None, except captions |
| Workbook fill | Salient Facts, the assessment grid, and the numeric skeleton of Cost, Sales, and Income | The workbook, read without Excel, rendered through the bridge | None |
| Structured extraction | Description of Improvements, Site Analysis facts, Neighborhood from the transcript | Assessor card, transcript, zoning and flood documents | Extract with a quote, Mark ticks |
| Data plus prose | Market Overview, the narrative of the approaches | ESRI spreadsheet, CoStar report, workbook | Write at length from numbers, behind Mark's edit |
| Boilerplate with slots | Title, Transmittal, Certification, Limiting Conditions, Statement of the Problem, Highest and Best Use skeleton, methodology paragraphs | The brief and the workbook conclusions | None |
| Binding | Table of contents, order, addenda, final PDF | Built sections | None |

Two consequences. The three approaches are not their own kind. They are
workbook fill plus data-plus-prose plus repetition, the largest compositions in
the report, which is exactly why the old system failed on them. And Market
Overview is the only place the model writes at length. It is a different risk
class from everything else, and the old rubric rated it yellow with no retail
donor in the corpus.

**What should exist once.** The evidence for each item is that it already
exists twice.

- **A section definition, as data.** Name, which shapes carry it, its kind of
  work, what it needs and from which folder or sheet, its template, its state
  store, its build. Today that knowledge is split across a typed string on the
  job screen, a planned-workflow row, the orphaned readiness table, the brief's
  empty donor column, and the matrix.
- **One job record.** The brief holds eight assignment fields in the job
  folder. Mark's corrections and photo folder choice sit in a home-folder file
  keyed by resolved path. The photo manifest holds the report year, caption
  style, photographs per page, and bands, which are job facts inside a section
  store. The Improvements state sits in another home file keyed the same way.
  Two homes, four stores. A job renamed or moved on the Z drive keeps its
  manifest and loses everything keyed by path, silently.
- **A fact ledger with provenance.** The Improvements layout file already says,
  per field, whether the value comes from the card, the transcript, both, Mark,
  or nowhere. Captions carry a reviewed tick. Classifications carry a state.
  Job facts carry a correction. These are four partial versions of one thing: a
  value, its source, its quote or cell, whether Mark confirmed it, and where it
  was used. That is the direct descendant of the old source trail and decisions
  file, and it is the abstraction every remaining section needs.
- **A source-document layer.** Find, rank, confine, and read a PDF, a Word
  file, a spreadsheet. The Improvements branch built it for two file kinds with
  filename hints. The old digest knew which 25 sheets matter and how to tell a
  blank workbook from template chrome. The bridge's extractor reads a range.
  Three readers, no shared layer.
- **One model call.** Client construction, key, no retries, structured parse,
  the error ladder, usage recording. Duplicated line for line between the
  caption module and the Improvements module.
- **One Word engine.** Reading a template's shape, repeating a block, fitting
  an image, filling a label, rewriting the year, keeping page numbers alive,
  merging orphan sections, naming the output, never overwriting. Today the
  photo engine has the furniture, naming, and table repetition. The
  Improvements engine has shape reading, block repetition, and field fill.
  Neither has the other's half, and the Improvements template has no footer at
  all while the photo templates carry a copyright year rewritten at build.
- **One review screen shell.** Sources, confirm the spend, review with ticks,
  build, open in Word. The photo screen and the Improvements screen are that
  shape twice.
- **Output checks.** The old standards check enforced em dashes, footer year,
  header repetition, and photo geometry on every built file. The app has those
  as tests only. A built file is never checked at build time.

### The architecture that should connect them

**What has moved into software, and what has not.**

| Responsibility | Old home | Now |
|---|---|---|
| Job creation, naming convention, folder shape | Onboarding skill, cloned template | Code, measured from the corpus |
| Section list per shape | Matrix plus popup | Matrix read at run time |
| Per-section readiness, "waiting on" | Readiness scan plus guides plus scoreboard | Lost. Folder inventory only |
| Memory, never ask twice | Decisions and conventions files | Stored answers, four stores |
| Photo triage, order, captions, pages | Script plus rules | Code, beyond the old |
| Never invent, flag do not settle | Instruction | Prompt rules, quote verification, refusals |
| Candidate values never picked | Instruction | No counterpart, no numbers flow yet |
| Chat interface | Scoreboard, one popup, banned words | Screens, a click leads to a step |
| Kit integrity | Byte audit of the kit | Manifest check of the package |
| Grading | Conductor and grader skills, human proctor | Tests against the corpus, hand checks |
| Excel and Word rendering | AppleScript, Spenser warming Office | Bridge on a branch, cold Office is a sentence |
| Delivery and updates | None | Package, install, update, rollback |
| Workbook reading, sentinels, chrome | Digest script | Not in the app |
| Binding, table of contents, addenda | Assembler script | Not in the app |
| Exhibit geometry per sheet | Exhibit script | Not in the app |
| Per-section input contracts, registers, spine tables, scenario rules, footer-year rule, caption grammar per shape | Recipes and matrix prose | Not in the app |
| Which photographs, effective age, condition, adjustments, which value is final, comp pin maps, how he sequences his own work | Mark | Mark |
| Filename prefixes as order and caption, subfolder conventions, the workbook's one-column-per-building layout | His files | His files, and the app now asks rather than reads |

**Domain knowledge against baggage, and the one that matters.** The
classification above holds for almost everything. One item deserves its own
paragraph. The old system started with "never settle a conflict, flag it" and
paid for it: 78 flags reached Mark in one run and about ten were genuinely his.
It then adopted a precedence rule. On a physical or recorded fact, building
size, year built, dates, parcel, the record beats the field note, the
resolution is written down, and drafting continues. Popups are reserved for
judgment and for gaps. The new Improvements plan says the app never settles a
disagreement. That reverses a measured lesson. The right shape is neither rule
alone. It is a per-field policy in the fact ledger: physical facts resolve to
the record and show the override, judgment stays Mark's, gaps stay blank. The
layout file already has the column for it.

**Where the current architecture will hurt as sections are added.**

- Two homes for job state, keyed two ways.
- Three route styles: inline in the main file, a router carrying its domain
  logic, and a router over engine modules.
- A build route whose refusal ladder is 150 lines of photo-specific code in the
  main file.
- The report year set to today's year at the first manifest write, per section,
  when the old rule is the publication year, per job.
- Two Word engines with disjoint halves and different furniture.
- The model client twice.
- The interface copying engagement lists, property types, a default state, a
  tranche size, and two brand colours.
- Two ways of knowing what a file is: nine labels Mark applies, and filename
  hints the Improvements reader uses.
- The section picker unreachable after creation.
- The matrix's scenario, property-type, and effective-date tables read by
  nobody.

None of these is wrong for one section. Each becomes a copied value the moment
there are two, and the copied-value defect is the one this project has now paid
for five times.

**The boundaries that are visible now.**

- Mark's files, the app's notes, and generated outputs: stated, enforced, with
  the photo manifest as the grandfathered exception because it is hand-editable
  and travels with the job.
- Deterministic against model: enforced by folder, since the engine has no
  model and the server has the model and the routes.
- Observed fact, Mark's judgment, model suggestion: visible for the first time
  as a per-field attribute in the Improvements layout, and it is the axis the
  whole report runs on.
- Job-wide against section-local facts: year, scenarios, buildings, tenancies,
  engagement, effective date, city and address are job facts, and today some
  live in a section store.
- Report shape against section: five shapes now, not four, with the land
  appraisal resting on one instance.
- Platform: one function answering "are we on Windows", used three times the
  same way.
- And the one boundary the old contract left open and the app has settled:
  Word is the editor, the app builds and gets out of the way, and nothing
  reaches into a built file.

**What the analysis makes unavoidable.** Not an order of sections. One fact:
whichever section comes second forces the section definition, the single job
record, the shared Word engine, and the fact ledger, because the second section
is where every one-off becomes a copy. The Improvements branch already shows
this. It reused the platform cleanly and rebuilt the section machinery from
scratch, and it is the section machinery that drifted 78 commits behind.

## Description of Improvements, measured (2026-08-28), recovered 17 September

**Recovered on 2026-09-17 from branch `improvements-section`**, where it was
`docs/ROADMAP.md:359-440`. It existed nowhere on `working`, and the branch is
parked and 160 commits behind, so it is copied here unchanged, below this note,
before the branch can be lost.

Two files from that branch came with it, byte for byte, taken with
`git show improvements-section:<path>`:

- `app/data/improvements-layout.md` is now at
  `docs/design/improvements/improvements-layout.md`.
- `app/templates/Improvements.docx`, the template approved as the governing
  source for the section (see the 2026-08-17 decisions above), is now at
  `docs/design/improvements/Improvements.docx`.

**They are under `docs/`, not `app/`, on purpose.** `tools/package_windows.py`
copies `app/data` and `app/templates` whole into the Windows package
(`APP_PARTS`, line 58), and nothing on `working` reads either file. Putting them
under `app/` would have changed what Mark receives. `docs/` is left out of the
package. When the section is built, the files move to `app/` with the code that
reads them. The layout file's first line still names `app/templates/`, because
it is the branch's copy and has not been edited.

Replaces an earlier attribution built from Mason City alone, which was wrong.
That job's Description of Improvements traces to the Clinton Walmart report in
its own `Old Reports` folder, and that report's text is Iowa City's. One job is
not a measurement, which is a rule this file already carried.

### Decided

- **Narrative1 is replaced, not fed.** Mark's workbook pushes values into Word
  through `DOCVARIABLE` fields (`BuildingsTotalGBA`, `Building1YearBuilt`,
  `BuildingsParkingSpaces`, `BuildingsLandtoBuildingRatio`,
  `BuildingsCapsuleDescription`), all present in both his documents and the
  workbook itself. The app neither writes into that chain nor reads it. It
  reads the sources and writes the document. Consequence: the app owns the
  arithmetic N1 used to do.
- **The section is built toward Blaul Lofts**, after Spenser spoke to Mark.
- **Mechanical Equipment and Site Improvements are in the layout** even though
  Blaul omits both, labels taken from 215 E 37th. Blaul's own transcript
  carries the mechanical detail its document does not print, so the omission is
  Mark's rather than the source's.
- **The template is authored, not stripped from a delivered report.** It is the
  layout, the file Spenser can open and change, and the yardstick the tests
  measure against, all as one artifact.

### Measured

- **No firm-wide layout exists.** Nine delivered reports carry the section and
  no two share a 60-character run of text, compared letters-only so PDF spacing
  cannot hide a match. The property-independent boilerplate appears in one
  report each.
- **The Mills Fleet Farm rack is one lineage, not a standard.** Its blocks
  (Overall Rating, Equipment and Mechanical, Interior Description, Remodeling,
  Building Floorplan) appear in 1 of those 9. It descends Iowa City to Clinton
  to Mason City to Mills. Do not propose it again as the template.
- **Blaul Lofts, 215 E 37th and Brookside are one layout family.** Foundation,
  Exterior Walls, Roof and Windows appear in all three with identical labels in
  identical order. That is the only hard spine in the corpus.
- **Where Blaul's values come from**, measured against its own assessor card
  and inspection transcript, both in the vault at
  `Report Examples/BURLINGTON_425 Valley St, (Blaul Lofts)`:

  | Source | Labeled fields, of 21 |
  |---|---|
  | Transcript alone | 9 |
  | Transcript and PRC together | 3 |
  | PRC alone | 1 |
  | One source plus a third | 3 |
  | Neither source | 4 |
  | Contradicts its own source | 1 |

  **The transcript is the primary source, not the assessor card.** The numbers
  split cleanly: four exact PRC reads (GBA 70,607, 39 units, built 1915, the
  7,672 fourth floor), two calculations (land to building, 21,294 / 70,607 =
  0.30 to 1; actual age from 1915), one from the lease (4,134 commercial
  suite), and two judgments that are always Mark's (effective age 20, remaining
  economic life 30).

- **Four fields have no source at all**: Store Fronts; Ceilings and Lighting
  under common areas; Parking under the commercial suite. They come out blank
  and marked. They are where a filler would invent.

- **Mark already performs the extraction step by hand.** The Blaul folder holds
  his raw dictation and a cleaned version reorganised under Building Exterior,
  Building Interior and Common Areas, Apartment Units, and Commercial and Event
  Spaces. Those are the document's own blocks. The seam the app needs is one he
  is already working.

- **Two drifts in the delivered document, found by attributing it.** Bathrooms
  says full baths in every unit; his transcript records three-quarter baths in
  four of the six units inspected. Kitchens says granite; the transcript says
  hard surface six times and never granite. Neither is large, and both are what
  a draft showing its sources would have caught. That is the argument for
  showing them.

### Owed

- The fill is unproven. Nothing reads a PRC or a transcript yet.
- The layout rests on three documents, one of which is not delivered work.
  Further apartment or mixed-use reports from Mark are worth more than any
  additional work against this corpus.

## Later

Far-off work taken off the checklist on 2026-09-17, so the checklist holds what
is next. One line each: what it is, why it is far off, and where this file
already reasons about it. Nothing here is approved to build.

- **The app suggests what a file is from its name, for him to confirm.** Not approved or designed, and it first needs a measurement of how often a name's prefix would be guessed wrong, which was its own checklist line and is folded in here. See "Still owed out of that work" above, and F10 in `docs/FUTURES.md`.
- **Offer to move a file to the part of the report it belongs in.** It runs against the rule that the app never touches Mark's folders, and Phase 4 has not yet decided whether sorting shows a category or moves a file. See Phase 4 below.
- **Select photographs across more than one folder.** Deliberately not built until he has wanted it twice. See "Still owed out of that work" above, and F11 in `docs/FUTURES.md`.
- **What happens when captions overflow a six-photograph page.** Not decided, and the worst page Mark's own two hundred captions can make still fits with 0.40 inch spare. See the 2026-09-07 decisions, "A test that fails by design is not a test".
- **Its own web address for updates instead of Cloudflare's.** One appraiser downloading now and then is nowhere near the development address's limit. See "Where updates will be pushed from, 2026-08-27".
- **Sign the package so it proves who built it.** The hash check guards against accident, not against an adversary, and that limit is already said on the screen where Mark decides. See "What the checking does and does not do, 2026-08-28".
- **The job screen says what information a job still needs.** It waits for the information-needs slice, and `readiness_scan.REQUIREMENTS` sits in the tree for it. See "Carried out of Phase 0" above, and the 8 September analysis, which names per-section readiness as something the app lost.
- **Find out which band names the office types, and whether clicking beat dragging.** A measurement of the office's own use, not a build, and it needs jobs made with bands to measure. It was the closing task of both 7 September band plans. See F6 in `docs/FUTURES.md`, which names the band vocabulary as unmeasured.

## The punch list

It lives in `docs/PUNCHLIST.md`. It is a work list, and this file is not one:
this file is context and decisions, read cold by somebody who was not in the
room. The reasoning behind an item stays here. What is left to do is there.


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

Off the checklist on 2026-09-17, where each was one line:

- The map and picture pages: aerial, neighborhood, plat, sketch, comp map
- The four boilerplate sections whose templates already exist
- Salient facts, which needs the workbook and a grid together

**Phase 3: the approaches.** Cost, Sales, Income. Each approach's
furniture comes from its own recipe and they do not share one structure:
Sales uses per-comparable pages in one variant only and has two other
measured variants; Income uses rent grids, survey exhibits, and operating
statements, with no per-comparable pages at all; Cost has its own ordered
block list. Grids come from the bridge. Template manufacturing at full
speed under the gate above. Longest phase.

Off the checklist on 2026-09-17, where each was one line:

- The three approaches: cost, sales and income

**Phase 4: the model's sections.** Prose drafting from dictation into
structured blanks Mark edits. The engagement letter into the intake form.
The one-drop intake. Everything degrades to typed-by-hand when there is no
key, the way captions already do. Do not explode this phase into a plan
until it has a truth-and-authority contract: which extracted fields are
observed facts and which are model suggestions, what requires Mark's
confirmation, what stays blank when extraction is uncertain, whether
sorting displays a category or moves a file, and where app-owned
classifications live without touching Mark's folders.

Off the checklist on 2026-09-17, where each was one line:

- Mark dictates and the app drafts the words into blanks he edits
- The engagement letter fills itself in from the job
- He drops all the documents in at once and the app sorts them

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

Off the checklist on 2026-09-17, where each was one line:

- The whole report: assembly, contents, addenda, the delivered file
- Rebuild one delivered job of each report shape, next to the original
- Mark gets everything through phase three in one handoff, not a drip
- The short form and the other report shapes, each from its own recipe

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

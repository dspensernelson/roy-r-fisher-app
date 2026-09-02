# The punch list, highest first

Work Spenser has decided on and parked. Highest priority at the top. Each item
says whether it is approved to build. Designed and approved are not the same
thing and the difference is the gate.

This is not a plan. A plan is a work list with a death date and it deletes
itself when its work is done. This outlives any one session, so it is a file of
its own rather than a section of `docs/ROADMAP.md`, which says of itself that
it is context and decisions and not a work list.

Items leave this file when they are built. What they teach on the way out goes
to `docs/ROADMAP.md`, which is where learnings live and the only document in
the repository meant to grow.

## 1. The photo screen looks broken on Mark's PC, 2026-09-02

**Approved 2026-09-02. Build this next, after the repository cleanup.**

Mark clicks Subject Photographs and the screen sits on loading. He cannot tell
whether it is working or dead, and neither can Spenser.

Measured from the code, not from his machine. His jobs sit on a network drive,
which is what makes each of these slow rather than merely wasteful:

- The screen shows nothing until `GET /api/jobs/{name}/manifest` returns.
  Every other call on that screen fails quietly, so that one call is the whole
  wait.
- `load_manifest` calls `exif_order` on every photograph it has not seen
  before. `exif_order` opens each image file to read its capture date. One job
  of Mark's holds 131 files.
- That route never saves what it worked out. So the dates are read again on
  every open of the job, not once.
- The black window prints nothing. `app/run_app.py` sets `log_level="warning"`
  and `access_log=False`, which is right for Mark and leaves Spenser with no
  evidence when something hangs on a machine he cannot see.

Three changes, in this order. The first one removes most of the wait.

1. **Save the manifest after the first read**, so the dates are read once. This
   removes the file opening. It does not remove the folder listing, which
   still runs on every open and is far cheaper.
2. **Say what is happening while it reads.** Approved: a sentence and a count,
   "Read 40 of 131", not a bare spinner. Spenser chose the count over a plain
   sentence on 2026-09-02.
3. **Write a log file on Mark's machine**, so he can send one instead of
   reading a window that says nothing.

**This is a rule already on record, applied to the second place it was always
needed.** The decision of 2026-08-28 says a progress bar that says nothing
looks like a hang, because his jobs are on a network drive. That was written
about the update download. The photo screen never got it.

**Open question, and it changes how bad this is.** Nobody has confirmed
whether Mark's jobs are on a network drive or on the PC's own disk. The
roadmap says network drive. It is the difference between a minute and ten.

**It can ship by the update button.** 0.6.0 carries the button, so 0.6.1 is
the first version Mark can take without a manual install. That makes it the
first real test of the button, which has never run on Windows. The zip and
`Install or update Roy R. Fisher.bat` remain the fallback.

## 2. Photo bands, 2026-09-02

**Designed 2026-09-02 with Spenser, in chat. Not approved to build.** The
design is here rather than in a plan because no slice has opened and a plan is
a work list with a death date.

Mark turns bands on, clicks one dot under each photograph, and the photo pages
come out arranged the way the property reads. One click per photograph instead
of one drag per photograph.

Three locked bands, A first, B middle, C last, whose position is their meaning
and which therefore never move. Typed bands slide anywhere between A and C,
never before A and never after C. Each tile grows one dot row: one dot per
band, then the Reviewed tick as the last dot, which is where the separate
`Mark Reviewed` button goes. The toggle and the band list are per job and live
in the manifest.

**Three constraints the build has to hold. They are the reason this works.**

1. **Turning bands on moves nothing.** Photographs already loaded sit in an
   unassigned strip and drain as Mark clicks. `photos.py` promises a human's
   ordering is never reshuffled and this keeps that promise. Build waits for
   the strip to empty, the gate `allReviewed` already uses.
2. **A band click resorts `manifest["photos"]` itself,** so array order always
   equals band order then position within band. The array stays the one
   ordering fact, and `photos.included()` and `build_photo_docx` change not at
   all. Bands must never become a second ordering system the build reconciles.
3. **A band's letter is assigned at creation and frozen.** First letter, then
   first two on collision, then three. Adding, renaming or deleting a band
   never relabels an existing one. Warehouse keeps W when Workshop arrives and
   takes Wo.

Edges decided the same day: a cut photograph keeps its band and sorts with it,
so uncutting restores its place; bands off reorders nothing; an empty on band
shows its header so Mark can see he still owes it photographs; deleting a band
returns its photographs to unassigned.

**These three constraints belong in a docstring and a test once the code
exists**, next to the one on `photos.included()`, which is the only place they
cannot drift from what they describe. Until then they are here.

Risks named before building: the dot row grows with every band on a screen
Spenser already called confusing, and nobody has measured which areas Mark's
reports actually use, which is why bands are typed rather than a fixed
vocabulary.

Absorbs two earlier wants. Moving a photograph to the front is one click on A,
now that the grid order is known to be the print order. The `Mark Reviewed`
button becomes the last dot in the row.

## 3. Click a photograph, see it bigger, 2026-09-02

Not designed. While captions are being written the thumbnail is too small to
check what is actually in the frame. Unrelated to bands.

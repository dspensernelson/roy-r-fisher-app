# Futures

Things we want. **Nothing is broken.** If something is broken today and
somebody is affected, it belongs in `docs/BUGS.md` instead.

Each item says whether it is approved to build. Designed and approved are not
the same thing, and the difference is the gate.

Items leave this file when they become a plan. What they teach on the way out
goes to `docs/ROADMAP.md`.

---

## F1. Spenser reads the log without asking anybody for it

**Three separate things, all wanted, stated 2026-09-03.**

1. `Show the log` shows the text on screen, with a `Copy` button.
2. It also sends Spenser a copy. Somebody pressing that button is somebody
   with a problem, so the log should travel without being asked.
3. Spenser can reach the log remotely, without Colleen sending anything.

Point 3 is the one that matters and the one that was traded away on
2026-09-02. The reasoning then was a day of work for a Cloudflare Worker. The
first real incident, the next morning, arrived as an email from Colleen with
the log pasted into it, which is exactly what Spenser said he did not want.

Needs a Worker so no password ships inside the package, and it moves client
property addresses off her machine. Both are decisions and neither is settled.

## F2. Mark all as reviewed

Wanted 2026-09-02, restated 2026-09-03 as something that has to exist.

**Behind a warning, not a plain button.** The words say plainly that this
removes the human check on what the model wrote. Cancel or continue, his
choice. Spenser's reasoning, in his own words: it is very important that humans
review everything AI does.

## F3. A way through, wherever the app refuses

**Working theory, Spenser, 2026-09-03: you should be able to force your way
through.**

The app raises 62 different refusals. Most of them are walls with no door. When
one of them is wrong, or the state behind it is wrong, there is nothing the
person in front of it can do.

This is the general form of B4. The narrow fix for the build is in the plan.
The general question, whether every refusal should offer a way past it, is not
decided and should not be decided by whoever happens to be writing the next
one.

## F4. A photo page that holds six, and the choice of which to use

Today every page holds three. Mark's office wants six, and wants to pick.

**The layout, specified by Spenser 2026-09-03.** Six photographs a page, three
down the left and three down the right, each pair of captions under its pair of
photographs. Reading left to right, top to bottom:

    photo    photo
    caption  caption
    photo    photo
    caption  caption
    photo    photo
    caption  caption

Mark may be able to send a template to build from, or it can be manufactured
the way `app/templates/Photo.docx` was.

## F5. Reset a job's photographs back to the start

Wanted 2026-09-03, after recovering from B6 meant deleting
`photo-manifest.json` by hand and risking every caption in it.

**Parked, deliberately, and here is what is unresolved.** Spenser's instinct is
that a reset keeps the captions and puts everything else back: the order the
photographs came in, nothing added, nothing taken out, no leftovers. That is
not the same as `Clear captions`, which must go on doing exactly what its name
says.

The hard part is that "back to the start" has no single meaning once a person
has added photographs, taken some out, and captioned others. **It is not
designed and must not be built until it is.**

---

## F6. Photo bands, 2026-09-02

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

## F7. Click a photograph, see it bigger, 2026-09-02

Not designed. While captions are being written the thumbnail is too small to
check what is actually in the frame. Unrelated to bands.

---

# Carried in from the roadmap, 2026-09-03

These five were only ever written in `docs/ROADMAP.md`, under "Still owed out
of that work". They are wants, so this is where they belong. **The roadmap
keeps the reasoning and the measurements behind each one**; only the want moves
here, so nothing is copied twice and left to drift.

## F8. A layout pass over the job screen and the photo screen

Spenser, 2026-08-25: it is all a little confusing. Not specified. F6 above is
part of this, not a replacement for it.

## F9. Taking several photographs out at once

Maquoketa carries four the office marked `Z` for do not use, and they come out
one click at a time. Bulk classify does not solve it: taking a photograph out
of a section is a question about the section, and that lives on the right of
the screen where there is no choosing-several yet.

## F10. Suggesting a classification from the filename, for him to confirm

Forbidden today. Reopened 2026-08-25 and the corpus supports it: his own naming
carries a type prefix far more often than not. Not approved, and it needs its
own measurement pass over how often a prefix would be wrong first. Proposing is
not asserting.

## F11. Selecting across more than one folder at once

Not built on purpose, 2026-08-25. It waits until he has wanted it twice.

## F12. Putting the way back somewhere Mark can find it

A bad update is undone by running the previous version's install file. That is
true and it is written down nowhere he would look.

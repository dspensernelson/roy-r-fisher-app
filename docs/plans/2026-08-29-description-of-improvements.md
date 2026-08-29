# Plan: Description of Improvements

Delete this file when the work is done. That is the last task.

## Goal

Mark opens a job, presses one button, and gets a Description of Improvements
Word file. The app reads his assessor card and his inspection transcript, fills
what it can, and shows him every value and where it came from before it writes
anything.

## Rules this work must follow

These are not suggestions. They came out of measuring nine of Mark's delivered
reports and one job's real sources.

1. **Never state a fact the app cannot observe.** A blank costs Mark ten
   seconds. A wrong value reaches his client.
2. **Every value shows its source.** Assessor card, transcript, calculated, or
   Mark. A value with no source is a defect.
3. **The app never settles a disagreement.** If the card and the transcript
   differ, show both and let Mark pick.
4. **Four fields have no source and stay blank**: Store Fronts; Ceilings and
   Lighting under common areas; Parking under the commercial suite.
5. **Mark's judgment is never filled by the app**: effective age, remaining
   economic life, condition, and all conclusion prose.
6. **Nothing prints before Mark sees a screen.**
7. **Never write into `Report Examples/`.**

## Layout

Blaul Lofts, plus the two blocks Blaul leaves out. Labels for those two come
from the 215 E 37th report.

| Block | Fields |
|---|---|
| GENERAL | prose only |
| BUILDING EXTERIOR | Foundation, Exterior Walls, Roof, Windows |
| BUILDING INTERIOR (repeats) | Walls, Ceilings, Floors, Kitchens, Bathrooms |
| MECHANICAL EQUIPMENT | HVAC, Electrical Service, Common Area |
| SITE IMPROVEMENTS | Parking, Trash Removal, Plantings, Sidewalks |
| CONCLUSION | prose only |

BUILDING INTERIOR repeats once per tenancy, per building, or per use. Blaul
uses three: Common Areas, Commercial Suite, Apartment Units.

Optional fields attach to a block and only appear when the job has them.

## Tasks

1. **Write the blank template**, `app/templates/Improvements.docx`. Every
   heading and label, no values. We author it. We do not strip a copy of one
   of Mark's reports. It is the layout, it is what Spenser opens to change a
   label, and it is what the tests measure against.
2. **Write `app/data/improvements-layout.md`.** Holds only what a Word file
   cannot: which source feeds each field, which blocks repeat, which fields
   are optional, which are Mark's judgment.
3. **Write `app/engine/improvements_pages.py`.** Copies the template, repeats
   the interior block as many times as the job needs, fills the values, saves.
   Plain Python. Runs the same on Windows.
4. **Read the assessor card and the transcript.** Pull out values. The model
   does this and nothing else. It does not settle disagreements and it does
   not write prose.
5. **Build the review screen.** Every field, its value, its source. Mark fixes
   what is wrong, then presses the button that writes the file.
6. **Turn the one hardcoded section name in `JobHome.jsx` into a real list.**
   Unavoidable once a second section exists.
7. **Tests.**
8. **Spenser clicks through the screen before it merges.**
9. **Debrief. Fold what we learned into `HOW-WE-WORK.md` and
   `docs/ROADMAP.md`. Delete this file.**

## Two layout rules found by building a mockup

Both go in the template. Neither is visible in Mark's own file.

- The page title repeats on every page automatically. Mark types his by hand,
  so it lands in the wrong place as soon as the text length changes.
- A block heading stays stuck to the fields under it. Without this, a heading
  ends one page and its contents start the next.

## Not in this slice

- No PDF of the finished report.
- No other section.
- No change to how Mark's folders are read.

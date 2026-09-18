# Now

The checklist. Read it first, every session. Add to it the moment Spenser asks
for something. Tick things off as they land.

Every item is one line. No paragraphs, no bug numbers: he works from the
published page, not from this file. `tools/build_the_checklist.py` turns this
file into that page and `app/tests/test_the_checklist.py` holds the rules.

**The first five headings are the north star**, one for each of his five
sentences, in his order. They come first because everything else is measured
against them. The work that moves a star sits under that star, so each one
shows how far along it is. Spenser asked for this on 2026-09-17: the starred
items are the important ones, and they were scattered.

**Every item names the north-star line it serves**, after a middle dot, or says
`No star`. That is how an item finds its heading: `Star 3` sits under the third.
The page does not draw it, because the heading above already says it. He asked
on 2026-09-16 for the star in everything, and the honest half of it is the
items where the answer is nothing: most of the work below does not touch the
star. Saying so out loud is the point. Silence would read as nobody having
thought about it.

**Every item stays under the heading it belongs to, ticked or not.** A ticked
item sits at the bottom of its own heading, below the open ones. There is no
`Done` heading in this file and nothing is ever moved out of a heading.

**The page generates the `Done` section.** It gathers every ticked item and
shows them together at the end, and each heading gets a line at its end that
pulls its own done items back up into it. It is generated because a person had
to remember to move an item when they ticked it, and nobody is reminded of that
rule. This file is the only place that knows where a done item came from, so
the file keeps it and the page does the gathering.

**Nothing appears under two headings.** The same work in two places is how a
thing gets built twice or argued about twice, and the test catches it.

**After the five stars, the order is time order, soonest first.** What needs a
decision from him, then the update the office is waiting for, then the area of
the report being built now, then the work he has asked for and not got, then
ideas nobody has confirmed, then housekeeping.

Spenser asked for that order on 2026-09-16, because he could not tell what was
next. The old headings sorted on three different questions at once: how big a
job is, who asked for it, and whether it was a bug. Where an item sat said
nothing about when it happens.

Detail lives in `docs/BUGS.md`, `docs/FUTURES.md`, `docs/PUNCHLIST.md`,
`docs/ROADMAP.md`, `docs/THE-WALK-2026-09-04.md` and `docs/CHECKS.md`. Far-off
work is in the `Later` section of `docs/ROADMAP.md`, and the report's sections
are in its phases.

## Press Update: the new app opens, the old one closes, nothing else happens

- [x] Confirm the fixed port is how we get to one tab · Star 1
- [x] An update must leave one tab: unproven until an update starts from 0.7.6.1 · Star 1
- [x] Prove an update Spenser can take himself, end to end · Star 1

## Double-click the icon: it opens, anything else running shuts down

- [ ] Mark unzips once and double-clicks a shortcut for ever · Star 2
- [x] Find out why every new version dies the first time it runs · Star 2
- [x] Start the background jobs after the web server, which is what killed it · Star 2
- [x] Starting the app must open one tab, not two · Star 2
- [x] The installer stops a running copy · Star 2
- [x] A console window sits in front of the app and stays there · Star 2
- [x] Nothing happens for a few seconds after you click the icon · Star 2

## Close the tab, or press Close the app: everything closes

- [ ] Closing the tab stops nothing: the app keeps running behind it · Star 3
- [ ] Close the app stops the app but leaves its tab open · Star 3
- [x] Close the app moved into the nav bar · Star 3

## Never shown an old screen or an old message

- [ ] Click the version: see what changed in it, and it checks for a newer one · Star 4
- [ ] What is the black window that appears after an update · Star 4
- [ ] The app looks for a new version on its own, and the version on screen says so · Star 4
- [x] Stop the green and red boxes piling up · Star 4

## The app never says anything it does not know

- [ ] Nothing tells you the new version started · Star 5
- [ ] The Make the Word file button does nothing, nothing is wired behind it · Star 5
- [ ] A log line at every step of starting up · Star 5
- [ ] A failed download says nothing until you have tried three times · Star 5
- [x] Clear captions leaves the ticks on, so Build is offered with no captions · Star 5
- [x] What should the loading page say when it cannot reach the app · Star 5
- [x] When Check now finds a version, an Update button appears beside it · Star 5
- [x] A failed update's reason is never written to the log · Star 5
- [x] Say what planned workflows means, or stop using the phrase · Star 5
- [x] Reviewed can never be more than written, read from one place · Star 5
- [x] The money is always there: an estimate first, then what it cost · Star 5
- [x] Make the launcher say what killed it instead of dying silently · Star 5
- [x] A photograph you removed stays in the list and blocks everything · Star 5
- [x] The photo screen sits on Loading for ever and hides the reason · Star 5
- [x] Show the log opens a window behind everything and says nothing · Star 5
- [x] Check now points at a button that is not on the screen · Star 5

## What needs you

- [ ] Errors found in signed reports, five so far: tell Mark, or not · No star
- [ ] Shorter words for Something else and the notes prompt, so they fit · No star
- [ ] What a switched-off button looks like: it has no fill and no edge · No star
- [ ] How far back should the log go · No star
- [ ] What does Reset put back · No star
- [ ] Which job produced the 700 KB photographs · No star
- [ ] Did the photographs widget replace the short list in the upper right · No star

## Get the office a working update

- [ ] The practice jobs live inside each version and are deleted three updates later · No star
- [ ] Nothing says why the app forgot which jobs folder was current · Star 5
- [ ] The photographs screen must be readable the way it is at 90 per cent · No star
- [ ] Trim the rules file, now 300 lines and growing every time a rule is stated · No star
- [ ] Run the 28 by-hand checks on Windows · No star
- [ ] Record who wrote each caption, so written and reviewed are two counts · No star
- [x] Every message box fills the width, the red error box included · No star
- [x] The written count includes photographs taken out of the report · No star
- [x] The photographs cover the bar of buttons on the photographs screen · No star
- [x] The update box must fill the width, not sit in a narrow box on the left · No star
- [x] The confirm box needs that same width fix · No star
- [x] Build the widget to the approved design, saved at docs/design · No star
- [x] Add photos becomes the photograph-and-plus icon · No star
- [x] Clear captions turns red and only appears when there is something to lose · No star
- [x] Mark all as reviewed leaves the left and becomes the check in the box · No star
- [x] Upload to the office · No star
- [x] The photographs screen, rebuilt to the approved design · No star
- [x] Settings, two columns, in his order · No star
- [x] The send-the-log button, built and merged · No star
- [x] Send the log to Spenser, connected end to end and proved with a real send · No star
- [x] The keystroke storm, the caption the tick ate, the price asked twice · No star
- [x] Add a photo puts the photograph where the report cannot see it · No star
- [x] Generating captions deletes photographs you added · No star
- [x] Taking out a photograph you added leaves a second copy behind · No star
- [x] Taking out one photograph takes the others with it · No star
- [x] Photographs added with the button do not appear · No star
- [x] Hitting Mark reviewed with the cursor in the box throws the caption away · No star

## Description of improvements

- [ ] Bring the parked engine, reader and template forward, and rebuild the screen · No star
- [ ] Build the approved drawing: sources, pill bar, widget, found and print · No star
- [ ] The job screen knows one section by name and needs a real list · No star
- [ ] Name the finished Word file the way the photo file is named · No star
- [ ] The template holds one building; each needs its own exterior and interior · No star
- [ ] The app suggests the buildings a PRC lists, and Mark confirms them · No star
- [ ] The app suggests which building each part of a transcript covers, Mark confirms · No star
- [ ] When the PRC and the transcript disagree, show both and Mark picks · No star
- [ ] Never fill his judgement: condition, quality, effective age, remaining life · No star
- [ ] Learn how Mark writes General and Conclusion from his delivered reports · No star
- [ ] Write General and Conclusion from approved facts and his notes only · No star
- [ ] Check that every fact in a written paragraph traces to one he approved · No star
- [ ] Area, land to building ratio and age rules fail on two buildings or parcels · No star
- [ ] Prior appraisals decide some fields; out of this slice, decide later · No star
- [ ] The print side still says Two answers, Pick one · No star
- [x] Save the 28 August measurement before the parked branch is lost · No star

## The report, section by section

- [ ] Re-run the Fable analysis once description of improvements reaches Mark · No star
- [ ] The report, phase by phase, is in the roadmap · No star

## You asked for it and it is not built

- [ ] Spenser reads the log without asking Colleen to send it · No star
- [ ] A way past it, wherever the app says no · No star
- [ ] A layout pass over the job screen · No star
- [ ] He types a band name and the band appears · No star
- [ ] He drags a band into place, renames it, or takes one away · No star
- [ ] A short list in the upper right saying what still needs doing · No star
- [ ] Subfolders · No star
- [ ] Read the city and address out of the job brief instead of refusing · No star
- [ ] The update screen feels up to date, the way TurboTax feels · No star
- [ ] Adopt the design system before there are more screens · No star
- [ ] A harness that renders a real screen out of the app, so a mockup is true · No star
- [ ] New job as two centred boxes · No star
- [ ] Manage active jobs · No star
- [ ] Clicking A, B or C shows only that band's photographs · No star
- [x] Mark uses his own key eventually, not Spenser's · No star

## Ideas nobody has confirmed with you

- [ ] Click a photograph and see it bigger · No star
- [ ] Take several photographs out at once · No star
- [ ] Ask Mark's office to stop shrinking photographs by hand · No star

## Housekeeping

- [ ] The photographs widget runs off the right edge at phone width · No star
- [ ] Packaging a version silently breaks whatever was pointed at the old one · No star
- [ ] Three plans on disk still have closeout tasks unticked · No star
- [ ] Nothing stops a version being published before the test machine has run it · No star
- [x] A test writes into the real log file instead of a temporary one · No star
- [x] Version numbering: four numbers for test builds, three for the office · No star
- [x] The checklist page is built by a file, not from memory · No star
- [x] Every recorded bug checked against the code: thirteen of sixteen fixed · No star

# Now

The checklist. Read it first, every session. Add to it the moment Spenser asks
for something. Tick things off as they land.

Every item is one line. No paragraphs, no bug numbers: he works from the
published page, not from this file. `tools/build_the_checklist.py` turns this
file into that page and `app/tests/test_the_checklist.py` holds the rules.

**Every item stays under the heading it belongs to, ticked or not.** A ticked
item sits at the bottom of its own heading, below the open ones. There is no
`Done` heading in this file and nothing is ever moved out of a heading.

**The page generates the `Done` section.** It gathers every ticked item and
shows them together at the end, and each heading gets a line at its end that
pulls its own done items back up into it. It is generated because a person had
to remember to move an item when they ticked it, and nobody is reminded of that
rule. This file is the only place that knows where a done item came from, so
the file keeps it and the page does the gathering.

**Every item names the north-star line it serves**, after a middle dot, or says
`No star`. He asked for that on 2026-09-16 and the honest half of it is the
items where the answer is nothing: the star describes an app that behaves like
an app, and most of the work below does not touch it. Saying so out loud is the
point. Silence would read as nobody having thought about it.

**Nothing appears under two headings.** The same work in two places is how a
thing gets built twice or argued about twice, and the test catches it.

**The order is time order, soonest first.** The north star is at the top
because everything else is measured against it. Then what needs a decision from
him, then the update the office is waiting for, then the area of the report
being built now, then the work he has asked for and not got, then ideas nobody
has confirmed, then housekeeping.

Spenser asked for this order on 2026-09-16, because he could not tell what was
next. The old headings sorted on three different questions at once: how big a
job is, who asked for it, and whether it was a bug. Where an item sat said
nothing about when it happens.

Detail lives in `docs/BUGS.md`, `docs/FUTURES.md`, `docs/PUNCHLIST.md`,
`docs/ROADMAP.md`, `docs/THE-WALK-2026-09-04.md` and `docs/CHECKS.md`.

## The north star

- [ ] Press Update: the new app opens, the old one closes, nothing else happens
- [ ] Double-click the icon: it opens, anything else running shuts down
- [ ] Close the tab, or press Close the app: everything closes
- [ ] Never shown an old screen or an old message
- [ ] The app never says anything it does not know

## What needs you

- [ ] How far back should the log go · No star
- [ ] What does Reset put back · No star
- [ ] Which job produced the 700 KB photographs · No star
- [ ] What is the black window that appears after an update · Star 4
- [ ] What should the loading page say when it cannot reach the app · Star 5
- [ ] Is description of improvements still the next major area · No star
- [ ] Is the parked description of improvements work brought forward or rebuilt · No star
- [ ] Who wins when the assessor card and the inspection transcript disagree · No star
- [ ] Is the 8 September Fable analysis the plan we build to · No star
- [x] Confirm the fixed port is how we get to one tab · Star 1

## Get the office a working update

- [ ] Every message box fills the width, the red error box included · No star
- [ ] The photographs screen must be readable the way it is at 90 per cent · No star
- [ ] Trim the rules file, now 300 lines and growing every time a rule is stated · No star
- [ ] An update must leave one tab: it did not on Windows, two are running · Star 1
- [ ] Nothing tells you the new version started · Star 5
- [ ] When Check now finds a version, an Update button appears beside it · Star 5
- [ ] Run the 28 by-hand checks on Windows · No star
- [ ] The photographs cover the bar of buttons on the photographs screen · No star
- [ ] Record who wrote each caption, so written and reviewed are two counts · No star
- [ ] Decide whether A B C stay in the box, and whether they filter · No star
- [x] The update box must fill the width, not sit in a narrow box on the left · No star
- [x] The confirm box needs that same width fix · No star
- [x] Say what planned workflows means, or stop using the phrase · Star 5
- [x] Build the widget to the approved design, saved at docs/design · No star
- [x] Reviewed can never be more than written, read from one place · Star 5
- [x] Add photos becomes the photograph-and-plus icon · No star
- [x] Clear captions turns red and only appears when there is something to lose · No star
- [x] The money is always there: an estimate first, then what it cost · Star 5
- [x] Mark all as reviewed leaves the left and becomes the check in the box · No star
- [x] Find out why every new version dies the first time it runs · Star 2
- [x] Start the background jobs after the web server, which is what killed it · Star 2
- [x] Make the launcher say what killed it instead of dying silently · Star 5
- [x] Prove an update Spenser can take himself, end to end · Star 1
- [x] Starting the app must open one tab, not two · Star 2
- [x] Upload to the office · No star
- [x] A photograph you removed stays in the list and blocks everything · Star 5
- [x] The photographs screen, rebuilt to the approved design · No star
- [x] Settings, two columns, in his order · No star
- [x] Close the app moved into the nav bar · Star 3
- [x] The send-the-log button, built and merged · No star
- [x] Send the log to Spenser, connected end to end and proved with a real send · No star
- [x] The installer stops a running copy · Star 2
- [x] The keystroke storm, the caption the tick ate, the price asked twice · No star
- [x] Add a photo puts the photograph where the report cannot see it · No star
- [x] Generating captions deletes photographs you added · No star
- [x] Taking out a photograph you added leaves a second copy behind · No star
- [x] Taking out one photograph takes the others with it · No star
- [x] Photographs added with the button do not appear · No star
- [x] The photo screen sits on Loading for ever and hides the reason · Star 5
- [x] Show the log opens a window behind everything and says nothing · Star 5
- [x] Check now points at a button that is not on the screen · Star 5
- [x] A console window sits in front of the app and stays there · Star 2
- [x] Hitting Mark reviewed with the cursor in the box throws the caption away · No star
- [x] Nothing happens for a few seconds after you click the icon · Star 2

## Description of improvements

- [ ] The Make the Word file button does nothing, nothing is wired behind it · Star 5
- [ ] The parked work is 142 versions behind and conflicts in four files · No star
- [ ] The job screen knows one section by name and needs a real list · No star
- [ ] Name the finished Word file the way the photo file is named · No star
- [ ] Save the 28 August measurement before the parked branch is lost · No star

## The report, section by section

- [ ] One definition of what a report section is, written down once · No star
- [ ] One record of what the app knows about a job · No star
- [ ] A ledger of facts that says where each value came from · No star
- [ ] One place that reads the source documents · No star
- [ ] One model call, not one for every section · No star
- [ ] One Word engine, not one for every section · No star
- [ ] One review screen that every section uses · No star
- [ ] Checks on the finished document, run when it is built · No star
- [ ] Whichever section comes second forces all of the above · No star
- [ ] The map and picture pages: aerial, neighborhood, plat, sketch, comp map · No star
- [ ] The four boilerplate sections whose templates already exist · No star
- [ ] Salient facts, which needs the workbook and a grid together · No star
- [ ] The three approaches: cost, sales and income · No star
- [ ] Mark dictates and the app drafts the words into blanks he edits · No star
- [ ] The engagement letter fills itself in from the job · No star
- [ ] He drops all the documents in at once and the app sorts them · No star
- [ ] The whole report: assembly, contents, addenda, the delivered file · No star
- [ ] Rebuild one delivered job of each report shape, next to the original · No star
- [ ] Mark unzips once and double-clicks a shortcut for ever · Star 2
- [ ] Mark gets everything through phase three in one handoff, not a drip · No star
- [ ] The short form and the other report shapes, each from its own recipe · No star

## You asked for it and it is not built

- [ ] The app looks for a new version on its own, and the version on screen says so · Star 4
- [ ] Spenser reads the log without asking Colleen to send it · No star
- [ ] A way past it, wherever the app says no · No star
- [ ] A layout pass over the job screen · No star
- [ ] The app suggests what a file is from its name, for him to confirm · No star
- [ ] He types a band name and the band appears · No star
- [ ] He drags a band into place, renames it, or takes one away · No star
- [ ] A short list in the upper right saying what still needs doing · No star
- [ ] Stop the green and red boxes piling up · Star 4
- [ ] Say which callout he has to act on · No star
- [ ] Offer to move a file to the part of the report it belongs in · No star
- [ ] Subfolders, and labelling several files at once · No star
- [ ] Read the city and address out of the job brief instead of refusing · No star
- [ ] The update screen feels up to date, the way TurboTax feels · No star
- [ ] Mark uses his own key eventually, not Spenser's · No star
- [ ] A goal conversation before each change, and a stop at the end of each phase · No star
- [ ] Adopt the design system before there are more screens · No star
- [ ] A walk of the photo screen with him before anything was designed on it · No star
- [ ] A harness that renders a real screen out of the app, so a mockup is true · No star
- [ ] New job as two centred boxes · No star
- [ ] Manage active jobs · No star
- [ ] The app guesses a job's name rather than asking him to type it · No star
- [ ] A log line at every step of starting up · Star 5

## Ideas nobody has confirmed with you

- [ ] Click a photograph and see it bigger · No star
- [ ] Take several photographs out at once · No star
- [ ] Select photographs across more than one folder · No star
- [ ] A strip holding the photographs still waiting for a band · No star
- [ ] Remember band names from the last job · No star
- [ ] Ask Mark's office to stop shrinking photographs by hand · No star
- [ ] What happens when captions overflow a six-photograph page · No star
- [ ] Its own web address for updates instead of Cloudflare's · No star
- [ ] Sign the package so it proves who built it · No star
- [ ] The job screen says what information a job still needs · No star
- [ ] Measure how often a name's prefix would be guessed wrong · No star
- [ ] Find out which band names the office types, and whether clicking beat dragging · No star

## Housekeeping

- [ ] Packaging a version silently breaks whatever was pointed at the old one · No star
- [ ] A failed download says nothing until you have tried three times · Star 5
- [ ] Three plans on disk still have closeout tasks unticked · No star
- [ ] Nothing stops a version being published before the test machine has run it · No star
- [x] Version numbering: four numbers for test builds, three for the office · No star
- [x] The checklist page is built by a file, not from memory · No star
- [x] Every recorded bug checked against the code: thirteen of sixteen fixed · No star

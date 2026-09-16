# Now

The checklist. Read it first, every session. Add to it the moment Spenser asks
for something. Tick things off as they land.

Every item is one line. No paragraphs, no bug numbers: he works from the
published page, not from this file. `tools/build_the_checklist.py` turns this
file into that page and `app/tests/test_the_checklist.py` holds the rules.

The order of the sections is the argument. The north star is first because
everything else is measured against it. What he said out loud outranks what a
session wrote to itself, and those two never share a heading.

Detail lives in `docs/BUGS.md`, `docs/FUTURES.md`, `docs/PUNCHLIST.md`,
`docs/ROADMAP.md`, `docs/THE-WALK-2026-09-04.md` and `docs/CHECKS.md`.

## The north star

- [ ] Press Update: the new app opens, the old one closes, nothing else happens
- [ ] Double-click the icon: it opens, anything else running shuts down
- [ ] Close the tab, or press Close the app: everything closes
- [ ] Never shown an old screen or an old message
- [ ] The app never says anything it does not know

## To get a version to the office

- [x] Find out why every new version dies the first time it runs
- [x] Fix it, which ticks north star 1 and 2: start the background jobs after the web server
- [x] Make the launcher say what killed it instead of dying silently
- [x] Prove an update Spenser can take himself, end to end
- [x] Starting the app must open one tab, not two
- [ ] An update must leave one tab, not two: the tab Update was pressed in never goes away
- [ ] The widget on the photographs screen must feel right-aligned, not left-aligned
- [ ] Everything on the photographs screen must be readable the way it is at 90 per cent
- [ ] Check now must offer the update there and then, not point at another button
- [ ] The update box must fill the width, not sit in a narrow box on the left
- [ ] Run the 28 by-hand checks on Windows
- [ ] Upload to the office

## Bugs still open

- [ ] A photograph you removed stays in the list and blocks everything
- [ ] The screen never closes after an update, and nothing says the new version started

## Description of improvements

- [ ] It goes on the right of the job screen, because it is part of the report
- [ ] Say what planned workflows means, or stop using the phrase
- [ ] Confirm Mark's template arrived: no plan is approved until it is inspected
- [ ] Decide whether the parked work is brought forward or built again
- [ ] The Make the Word file button does nothing, nothing is wired behind it
- [ ] The parked work is 142 versions behind and conflicts in four files
- [ ] The job screen knows one section by name and needs a real list before a second
- [ ] Name the finished Word file the way the photo file is named
- [ ] Decide who wins when the assessor card and the inspection transcript disagree
- [ ] Move the 28 August measurement into the roadmap before the parked branch is lost

## The Fable plan

- [ ] Decide whether the 8 September Fable analysis is the plan we build to
- [ ] One definition of what a report section is, written down once
- [ ] One record of what the app knows about a job
- [ ] A ledger of facts that says where each value came from
- [ ] One place that reads the source documents
- [ ] One model call, not one for every section
- [ ] One Word engine, not one for every section
- [ ] One review screen that every section uses
- [ ] Checks on the finished document, run when it is built
- [ ] It says whichever section comes second forces all of the above

## Waiting on Spenser

- [ ] Confirm the fixed port is the way to one tab through an update
- [ ] How far back should the log go
- [ ] What does Reset put back
- [ ] Which job produced the 700 KB photographs
- [ ] The black window after an update
- [ ] What the loading page should say when it cannot reach the app

## He asked for it and it is not built

- [ ] Spenser reads the log without asking Colleen to send it
- [ ] A way past it, wherever the app says no
- [ ] A layout pass over the job screen
- [ ] The app suggests what a file is from its name, for him to confirm
- [ ] He types a band name and the band appears
- [ ] He drags a band into place, renames it, or takes one away
- [ ] A short list in the upper right saying what still needs doing
- [ ] Stop the green and red boxes piling up
- [ ] Say which callout he has to act on
- [ ] The job screen offers to move a file to the section it belongs in
- [ ] Subfolders, and labelling several files at once
- [ ] The app reads the city and address out of the job brief instead of refusing
- [ ] The update screen feels up to date, the way TurboTax feels
- [ ] Mark uses his own key eventually, not Spenser's
- [ ] A goal conversation before each change, and a stop at the end of each phase
- [ ] Adopt the design system before there are more screens

## The report, section by section

- [ ] More than one section can be built, not just subject photographs
- [ ] The map and picture pages: aerial, neighborhood, plat, sketch, comp map
- [ ] The four boilerplate sections whose templates already exist
- [ ] Salient facts, the first section that needs the workbook and a grid together
- [ ] The three approaches: cost, sales and income
- [ ] Mark dictates and the app drafts the words into blanks he edits
- [ ] The engagement letter fills in the job's information
- [ ] He drops all the documents in at once and the app sorts them
- [ ] The whole report: assembly, contents, addenda, the delivered file
- [ ] The app rebuilds one delivered job of each report shape, next to the original
- [ ] Mark unzips once and double-clicks a shortcut for ever
- [ ] Mark gets everything through phase three in one handoff, not a drip
- [ ] The short form and the other report shapes, each from its own recipe

## Promised to him and not delivered

- [ ] A walk of the photo screen with him before anything is designed on it
- [ ] A harness that renders a real screen out of the app, so a mockup is true
- [ ] New job as two centred boxes
- [ ] Manage active jobs
- [ ] The app guesses the file name
- [ ] A log line at every step of starting up

## Ideas nobody has confirmed with him

- [ ] Click a photograph and see it bigger
- [ ] Take several photographs out at once
- [ ] Select photographs across more than one folder
- [ ] A strip holding the photographs still waiting for a band
- [ ] The app remembers band names from the last job
- [ ] Ask Mark's office to stop shrinking photographs by hand
- [ ] What the app does when captions overflow a six-photograph page
- [ ] Its own web address for updates instead of Cloudflare's
- [ ] Sign the package so it proves who built it
- [ ] The job screen says what information a job still needs
- [ ] Measure how often a file name's prefix would be wrong
- [ ] Find out which band names the office types, and whether clicking beat dragging
- [ ] Check the confirm box is the same width fix as the update box

## Housekeeping

- [ ] Trim the rules file, now 300 lines and growing every time a rule is stated
- [ ] Three plans on disk still have closeout tasks unticked
- [ ] Nothing stops a version being published before the test machine has run it

## Done

- [x] The photographs screen, rebuilt to the approved design
- [x] Settings, two columns, in his order
- [x] Close the app moved into the nav bar
- [x] The send-the-log button, built and merged
- [x] Send the log to Spenser, connected end to end and proved with a real send
- [x] The installer stops a running copy
- [x] The keystroke storm, the caption the tick ate, the price asked twice
- [x] Version numbering: four numbers for test builds, three for the office
- [x] The checklist page is built by a file, not from memory
- [x] Every recorded bug checked against the code: thirteen of sixteen already fixed

## Bugs already fixed, checked against the code

- [x] Add a photo puts the photograph where the report cannot see it
- [x] A new version dies the first time it runs, with no window and no message
- [x] Generating captions deletes photographs you added
- [x] Taking out a photograph you added leaves a second copy behind
- [x] Taking out one photograph takes the others with it
- [x] Photographs added with the button do not appear
- [x] The photo screen sits on Loading for ever and hides the reason
- [x] Show the log opens a window behind everything and says nothing
- [x] The app opens behind the black window
- [x] Check now points at a button that is not on the screen
- [x] A console window opens in front of the app and stays there
- [x] Hitting Mark reviewed with the cursor still in the box throws the caption away
- [x] Nothing happens for a few seconds after you click the icon

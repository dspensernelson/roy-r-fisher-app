# Now

The checklist. Read it first, every session. Add to it the moment Spenser asks
for something. Tick things off as they land.

Every item is one line. No paragraphs, no bug numbers: he works from the
published page, not from this file. Detail lives in `docs/BUGS.md`,
`docs/PUNCHLIST.md`, `docs/THE-WALK-2026-09-04.md` and `docs/CHECKS.md`.

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
- [ ] Starting the app must open one tab, not two
- [ ] Check now must offer the update there and then, not point at another button
- [ ] Run the 28 by-hand checks on Windows
- [ ] Upload to the office

## Waiting on Spenser

- [ ] Cloudflare setup so Send the log to Spenser works
- [ ] How far back should the log go
- [ ] What does Reset put back
- [ ] Which job produced the 700 KB photographs
- [ ] The black window after an update
- [ ] What the loading page should say when it cannot reach the app

## After that

- [ ] Make the screen close itself after an update, which ticks north star 4
- [ ] Strike off the bugs already fixed, because nobody has checked the list against the code
- [ ] Trim the rules file, now 280 lines and growing every time a rule is stated
- [ ] Five things from the 4 September walk, on the job screen and the update screen

## Done

- [x] The photographs screen, rebuilt to the approved design
- [x] Settings, two columns, in his order
- [x] Close the app moved into the nav bar
- [x] The send-the-log button, built and merged
- [x] The installer stops a running copy
- [x] The keystroke storm, the caption the tick ate, the price asked twice
- [x] Version numbering: four numbers for test builds, three for the office

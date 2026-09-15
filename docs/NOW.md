# Now

The checklist. Read it first, every session. Add to it the moment Spenser asks
for something. Tick things off as they land.

Detail lives in `docs/BUGS.md`, `docs/PUNCHLIST.md`,
`docs/THE-WALK-2026-09-04.md` and `docs/CHECKS.md`.

## The north star

It should behave like a real app. Written up in `HOW-WE-WORK.md`. None of these
is true today.

- [ ] Press Update: the new app opens, the old one closes, nothing else happens
- [ ] Double-click the icon: it opens, anything else running shuts down
- [ ] Close the tab, or press Close the app: everything closes
- [ ] Never shown an old screen or an old message
- [ ] The app never says anything it does not know

## To get a version to the office

- [x] Find out why 0.7.5 dies on startup
- [ ] Fix it: start the background jobs after the web server, not before
- [ ] Make the launcher say what killed it instead of dying silently
- [ ] Prove an update Spenser can take himself, end to end
- [ ] Run the 28 by-hand checks on Windows
- [ ] Upload to the office

## Waiting on Spenser

- [ ] Cloudflare setup so `Send the log to Spenser` works
- [ ] How far back should the log go
- [ ] What does Reset put back
- [ ] Which job produced the 700 KB photographs
- [ ] The black window after an update

## After that

- [ ] Strike off the bugs already fixed. The list holds fifteen and several were
      fixed weeks ago and never crossed out. Nobody has checked it against the
      code.
- [ ] Trim the rules file. It is 280 lines and grows every time Spenser states
      a rule. The rules are right; the file is becoming unreadable.
- [ ] Five things from the 4 September walk, on the job screen and the update
      screen

## What overlaps, so nothing is done twice

- **The first-run crash is two of the five north star lines at once.** Every new
  version dying the first time it runs is what breaks both Update and the icon.
  Fixing that one thing ticks both.
- **"Nothing happens for a few seconds after you click the icon" is the same
  crash**, reported separately weeks ago.
- **"The screen never closes after an update" is the north star line about never
  being shown an old screen.**
- **So the first-run crash is the first fix**, and it is the largest single move
  available.

**Bug numbers are for `docs/BUGS.md` only.** Spenser works from the checklist
and does not open the markdown. A thing on this page is named in words or it is
not on this page.

## Done

- [x] The photographs screen, rebuilt to the approved design
- [x] Settings, two columns, in his order
- [x] `Close the app` in the nav bar
- [x] The send-the-log button, built and merged
- [x] The installer stops a running copy
- [x] The loading page stops lying
- [x] The keystroke storm, the caption the tick ate, the price asked twice
- [x] Version numbering: four numbers for test builds, three for the office

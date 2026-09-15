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

- [ ] Close the bugs that are already fixed. The list says 15 and several were
      fixed weeks ago and never struck off. B13 was fixed 2026-09-14. B7 went
      with the send-the-log work. B8 and B11, the black window, went in 0.6.5.
      Nobody has checked the list against the code.
- [ ] Trim `HOW-WE-WORK.md`. It is 280 lines and growing every time Spenser
      states a rule. The rules are right; the file is becoming unreadable.
- [ ] 5 items from the 2026-09-04 walk, on the job screen and the update screen

## Where these overlap, so nothing is done twice

- **B15 is north star 1 and 2.** Every new version failing its first run is
  what breaks both Update and the icon. Fixing it ticks two of the five.
- **B14 is B15.** "Nothing happens for a few seconds after you click the icon"
  is the same cold start, reported separately.
- **B10 is north star 4.** The screen that never closes after an update is the
  old screen he must never be shown.
- **So the first fix is B15**, and it is the largest single move available.

## Done

- [x] The photographs screen, rebuilt to the approved design
- [x] Settings, two columns, in his order
- [x] `Close the app` in the nav bar
- [x] The send-the-log button, built and merged
- [x] The installer stops a running copy
- [x] The loading page stops lying
- [x] The keystroke storm, the caption the tick ate, the price asked twice
- [x] Version numbering: four numbers for test builds, three for the office

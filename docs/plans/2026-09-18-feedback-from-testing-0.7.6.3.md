# Feedback from testing 0.7.6.3

Spenser's running list while he works through the photographs slice checks on
the virtual machine, 18 September 2026. Batched, so one builder fixes it all
at once instead of one agent per remark.

Delete this file when the batch is fixed and merged. That is the last task.

## Done on branch `the-widget-says-what-it-means`, merged 18 September

- [x] "11 of 12 reviewed" shows a tick although not everything is reviewed.
- [x] A, B and C appear only when Bands is switched on. They should always
      be there, greyed when Bands is off, so nothing moves.
- [x] "5 of 5 reviewed" goes to done while 17 photographs have no caption,
      and after typing one caption it thought there was only one to review.
      Spenser chose: count every photograph in the report, typed captions
      counted as reviewed. "5 of 17 reviewed" is right.
- [x] The done state of the reviewed pill is a dark green he does not like.
      Use the light tick green `#3A8F52` on a pale tint.
- [x] Check that typing a caption drops the count on Generate captions.
- [x] Found on the way: the done pill sat 6.7px below the bar. Fixed.

## Batched, built and merged into `working` 18 September

- [x] The "Writing captions · 0 of 12 written" line under the title: make its
      progress bar longer. It is a short stub today.

- [x] **A rule for the widget's bottom bar.** Spenser: "We need to be careful
      with this box because I think it's becoming a catch-all." Before anything
      new goes in the bar, something has to come out or it goes elsewhere.
      Write this into HOW-WE-WORK.md with the bar's current contents listed.

- [x] **Back on a photograph does not work.** First find out whether it is a
      fault or the design: today Back only returns a caption that Clear
      captions wiped, so after a Refresh it has nothing to return.
- [x] **Refresh needs a sign that it is working**, on the photograph itself,
      while its one caption is being written.

- [x] **The title and widget row stays put at the top of the photographs
      screen while he scrolls**, with a red line under it running the full
      width of the screen, so what is happening is always in view. His words:
      "a static kind of progress bar."

## Decided by Spenser, 18 September, to build in this batch

- [x] **Back undoes a Refresh too.** Refresh keeps the words it replaced, and
      Back puts them back, the same way it does after Clear captions.
- [x] **The red line under the fixed row is a plain line**, in the app's red,
      full width, marking where the fixed part ends. Not a progress bar.
- [x] **A photograph moved to another band stays in the filtered view** until
      the filter changes or clears.
- [x] **The tick green goes a shade darker**, enough to read as small text on
      its pale background.

## From his check results, 18 September, to build in this batch

All 28 checks passed. The two he could not run, a stopped update writing its
reason to the log and the loading page when the app does not answer, stay
unverified on Windows.

- [x] Build photo pages and Generate captions slightly wider.
- [x] **A switched-off button: same colour, faded.** Build stays red and
      Generate stays blue, faded, and resting on it still says why. Replaces
      the pale fill with a coloured edge.
- [x] **Refresh shows "Refreshing caption" on the photograph** while its
      caption is written, and it goes away when done. His words.
- [x] **AI or Typed moves to the upper left corner of the photograph.** On
      the caption line it pushes everything down.
- [x] **Check now's answer sits to the right of the button**, not under it.
- [x] **The whole update happens inside the version card in Settings**, not
      in a box above everything.

## Waiting on Spenser

- [ ] Clicking the version badge shows plain-words notes for that version and
      checks for a newer one. Recommendation: the notes are written when each
      version is cut. Drawing to come.

## Later, not this batch

- [ ] The widget now takes more room than the title side on the left. Make the
      header tighter. Spenser: "let's just leave it for now."

## When the batch is done

- [ ] Fold anything learned into `HOW-WE-WORK.md` and `docs/ROADMAP.md`.
- [ ] Delete this file.

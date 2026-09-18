# Feedback from testing 0.7.6.3

Spenser's running list while he works through the photographs slice checks on
the virtual machine, 18 September 2026. Batched, so one builder fixes it all
at once instead of one agent per remark.

Delete this file when the batch is fixed and merged. That is the last task.

## Done on branch `the-widget-says-what-it-means`, not merged

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

## Batched, not yet sent

- [ ] The "Writing captions · 0 of 12 written" line under the title: make its
      progress bar longer. It is a short stub today.

- [ ] **A rule for the widget's bottom bar.** Spenser: "We need to be careful
      with this box because I think it's becoming a catch-all." Before anything
      new goes in the bar, something has to come out or it goes elsewhere.
      Write this into HOW-WE-WORK.md with the bar's current contents listed.

- [ ] **Back on a photograph does not work.** First find out whether it is a
      fault or the design: today Back only returns a caption that Clear
      captions wiped, so after a Refresh it has nothing to return.
- [ ] **Refresh needs a sign that it is working**, on the photograph itself,
      while its one caption is being written.

- [ ] **The title and widget row stays put at the top of the photographs
      screen while he scrolls**, with a red line under it running the full
      width of the screen, so what is happening is always in view. His words:
      "a static kind of progress bar."

## Waiting on Spenser

- [ ] The red line under the fixed row: does it fill as the job gets done,
      like a progress bar, or is it a plain line marking where the fixed part
      ends?
- [ ] Should Back undo a Refresh? Recommendation: Refresh keeps the words it
      replaced, and Back puts them back, the same way it does after a clear.
- [ ] A photograph moved to another band leaves the filtered view straight
      away, which feels abrupt. Recommendation: it stays until the filter
      changes.
- [ ] Clicking the version badge shows plain-words notes for that version and
      checks for a newer one. Recommendation: the notes are written when each
      version is cut. Drawing to come.

## Later, not this batch

- [ ] The widget now takes more room than the title side on the left. Make the
      header tighter. Spenser: "let's just leave it for now."

## When the batch is done

- [ ] Fold anything learned into `HOW-WE-WORK.md` and `docs/ROADMAP.md`.
- [ ] Delete this file.

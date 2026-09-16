# The photographs widget, approved 2026-09-16

**`photos-widget.html` beside this file is the design, and it wins over
anybody's judgement, including mine.** Open it. Every state is drivable from
the panels underneath: Written, Reviewed, Bands, Band letters. What it shows is
what was approved, not a drawing of it: the tokens, the sizes and the tick are
read out of `app/web/src/brand.css` and `PhotosScreen.jsx`.

He arrived at it by moving the pieces himself over about ninety minutes. The
numbers below are his, not proposals.

## The box

360 wide, 110 tall. Two rows and a bar joined to the bottom edge.

**Top row is spread, not right.** Build photo pages hard left, Generate
captions hard right. This matters beyond looks: spreading it is what puts Build
against the left edge, which is what puts the photo button directly underneath
it on the row below. Right-justifying floats Build inward and the button sits
under nothing. That was got wrong twice.

**Second row, right-justified**, with the photo button pushed hard left by
`margin-right:auto`: the photo button, Per page 3 or 6, the Bands switch, then
A B C.

**Add photos is an icon**, a photograph with a plus. Glyph 23px tall, the plus
carried 2 units right of the photograph inside a widened canvas. Not the words.

## The bar

It answers **how do I get to done**. It is not a notification pane. His words:
general notifications stay on the left where they already are. The moment the
two merge, the box becomes something to clear rather than something to read.

Left to right: the counts, then `✓ all`, then Clear captions, then the money
hard right against the box's own 14px padding.

**Everything in it is a pill**, and they all take their shape from the money,
which was the first one and set the language: 999 radius, a 1px edge at about a
third strength, a breath of the same colour behind, bold number and quiet word.
Nothing wraps and nothing shrinks: every pill is `flex:none` and `nowrap`, and
so is the bar. If it stops fitting it has to say so, not fold.

## Two counts, never one

**Written** is how many captions exist. **Reviewed** is how many Mark has
ticked. Reviewed can never exceed written, and both are read from one place.
They were two unrelated pieces of state once and the left of the screen said
"9 of 12 reviewed" while the box said everything was done.

**A slot changes job when its job is finished.** While captions are still being
written, the first pill reports writing. The moment every one is written,
writing has nothing left to say, so that slot stops reporting and starts
offering `✓ all`. Reviewed keeps counting beside it. When reviewed catches up,
the offer goes and one pill is left saying `✓ All reviewed`.

The glyph, never the words. That instruction was overwritten twice.

## Colour, and what it now means here

- **Red** belongs to exactly two things: Build photo pages, which writes into
  Mark's folder, and Clear captions, which destroys typing. Both cannot be
  taken back. Clear captions is a red link, not a button: "the same exact
  thing, just red."
- **Light green** is an offer. `✓ all` wears the money's exact green until it
  is pressed, because a filled pill reads as something that already happened.
- **Filled green** is a finished fact, and only `✓ All reviewed` gets it.
- **Amber** is something still to do.
- **Money is green**, "because it's money". `~6¢` while it is an estimate, and
  the tilde comes off once it is what the job has actually cost.

## What only appears when it is true

- **Clear captions** does not exist until there is a caption to lose.
- **The money is always there.** Before anything is generated it is the
  estimate, which is the one moment she most wants it. Hiding it then was an
  error of mine that he caught.

## Still open, and his to settle

- Whether A B C stay in the box at all, and whether they become a filter, which
  is the thing that would earn them the space.

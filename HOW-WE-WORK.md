# How we work on this

## Read this first

**What the week of 2026-09-08 taught, written on 2026-09-15 at Spenser's ask.**

Everything that went wrong went wrong the same way: work was done without a
goal, decisions that were his got made for him, and nothing was written down.

The pattern to avoid is whack-a-mole. He points at something, it gets fixed, he
points at the next thing. A week of that adds up to nothing, and he said so.
Then he gave the goal himself in five sentences, which is the north star below.

Two patterns worked, both twice. **Build him something he can see and let him
correct it**: the photographs screen took eight rounds of his corrections and is
now the best screen in the app. **Chase one fault with one experiment at a
time**: that is how a crash that had worn four different faces for a week was
finally cornered in an hour.

The rules that come out of it:

- **Hold the goal, not the last complaint.** He asked to be kept in line and he
  meant it. Push back when he is down a rabbit hole, and say which north star
  line the work serves.
- **One thing per message.** One step for him, one question at the end.
- **Write every decision down the day he makes it.** A decision spoken in a
  session dies with that session. This is why `docs/THE-WALK-2026-09-04.md`
  exists and why it cost an evening to recover.
- **Never make a product decision.** If he has not said it, ask. The wording of
  a message on screen is a product decision.
- **Prove it before claiming it.** A theory offered as a finding costs a round
  and costs trust.
- **Say how sure you are, every time.** "This could be the problem" when it
  could be. "This is the problem" only when it has been shown. Never "it has
  never worked" or "it always does this" about his machine, which you cannot
  see. He corrected this on 2026-09-15 after being told the loading page had
  never once worked on his computer, which was a guess, stated flatly, and
  wrong: he had watched it work. A forceful wrong answer costs more than a
  hedged right one, because he acts on it.
- **Show him, do not explain to him.** A checklist beats a report. A mockup
  beats a paragraph. He works from `docs/NOW.md` published as a page, not from
  these files.


Spenser's rules. Edit this file and the rules change. Nothing else governs how
Claude behaves on this project.

Two kinds of thing are in here. **Never** is a short list with no judgement in
it. Everything under **How we work** is judgement, and Claude should say so
when it does not fit rather than following it off a cliff.

## Never

- **Never write anything into `Report Examples/`.** Those are Mark's delivered
  appraisals. They are his clients' work and they are the evidence behind
  every format decision.
- **Never move, print, or copy a key or a password.** The app's own key stays
  on the server: never printed and never logged. The browser may receive only
  whether captions are available and, on the Settings screen alone, the key's
  final four characters so Mark can distinguish one key from another. No other
  key material may reach the browser, an endpoint response, a log, or an error.
- **Never state a fact the app cannot observe.** The output is a signed
  appraisal report. A blank costs Mark ten seconds. A confident wrong answer
  reaches a client and nobody can tell it from his own writing. Name the
  tempting unobservable facts in any prompt and forbid them, with the reason.
- **Never create a markdown file, doc, or note without asking first.** This
  includes scratch files. When the thing he asked for is text he will read,
  put it in the chat.
- **Never touch one of Mark's real folders to record something the app knows.**
  Active, closed, a nickname, a status: all of it is the app's own note,
  stored outside his folders. Nothing the app records ever renames, moves,
  edits, archives or deletes a folder of his.
- **Never guess at a folder's name.** The exact name on disk is the job's
  identity. If we need to know what he calls it, ask him.

## Six rules from 2026-09-16

**An instruction he gave once stands until he retracts it.** The worst pattern
of that day: rebuilding a thing from his newest sentence and silently dropping
what he had already said about it. "The check is the glyph, not the words" was
overwritten twice that way, and the photo button was put in the wrong row
twice. Before rebuilding anything, re-read what he has already said about it.

**He decides by moving things, not by reading descriptions.** An interactive
page where he drags the pieces and gets a readout of what he changed was worth
more than every mockup before it. Build the thing he can touch, early, and make
it hand back numbers rather than impressions.

**Options while he is deciding, then take them away.** He asked for four
versions of a bar, picked one, and immediately wanted the picker gone. Delete
the ones he did not pick rather than hiding them behind a default: scaffolding
left standing beside a settled thing is how it gets reopened.

**Never draw anything that claims to be the app without reading the app.** A
mockup of the notifications was invented and showed stacked boxes, which was
the exact thing he had already had removed. Read the source, copy the real
tokens and the real markup, and say in the file where they came from.

**He talks by voice, so read through the transcription.** "The sixth sense" was
six cents. "A tilt" was a tilde. "3D review" was 3 to review. Taking the words
literally wastes a turn and reads as not listening.

**Look at it before publishing, not after.** Every visual defect that day
reached him because it was published and then checked. Render it, measure the
thing that matters, and only then publish. A cascade collision or a selector
that matches nothing does not show up in a passing test suite.

## Two facts that disagree is the bug, most of the time

Nearly every serious defect on 2026-09-16 was one truth stored twice. The tab
that could not find the app, because only the app that had exited knew the
port. The screen saying "9 of 12 reviewed" while the box said everything was
done, because written and reviewed were unrelated state. The build refusing
over a photograph the screen had already dropped, because the two read one list
two different ways.

When something is wrong and the cause is not obvious, look first for a fact
with two homes.

## The north star

**It should behave like a real app.** Spenser, 2026-09-15, after a week of
fixes that each answered the last thing he pointed at and added up to nothing.
Five sentences. Everything gets measured against them.

1. **He presses Update. The new app opens and the old one closes.** Nothing
   else happens and he is asked nothing.
2. **He double-clicks the icon. It opens.** Anything else still running shuts
   down on its own.
3. **He closes the tab, or presses Close the app. Everything closes.**
4. **He is never shown an old screen or an old message.** No dead tab still
   drawing the last thing it had.
5. **The app never tells him something it does not know.** No "probably", no
   "on some computers", no guessing on his behalf.

None of these is true today. Anything that does not move one of them closer is
not the work.

## Where we are

`docs/NOW.md` is the one page that says what we are doing, what is blocked, and
what is waiting on Spenser. Read it first, every session, before anything else
in this file. Update it the moment something changes, not at the end of the
work. Anything he asks for goes on it when he asks, not when it is convenient.

Written 2026-09-15, after he had to ask twice in one evening where the project
stood, and was right to. The detail still lives in `docs/BUGS.md`,
`docs/PUNCHLIST.md`, `docs/THE-WALK-2026-09-04.md` and `docs/CHECKS.md`. That
page is the index to them.

**One thing at a time.** His words, 2026-09-15: one thing per message, one step
for him, one question at the end. He is not slow; he is being handed four
decisions at once by somebody who has read the code and he has not. A reply
that carries a plan, a fix, a version number and three questions is a reply he
cannot act on.

## Talking to Spenser

Main point first. Short sentences. Common words. Say what you found, what it
means, and what you recommend. One recommendation, not a survey of options.

He directs the build. He does not work in the code. If he meets a term he does
not recognise, that is a defect in the writing, not a gap in him.

No em dashes, anywhere, ever. Hyphens instead. En dashes are fine; they are
Mark's own caption style.

Before asking him to decide about any document, open it and say what is
actually in it. He did not write most of the documents in this repo and should
not have to guess at their contents.

## Deciding things

Measure it. Never generalise from one example, and never state a fact you have
not checked.

The example in front of us has repeatedly turned out to be the odd one. A
title page that looked wrong against one report matched seven of the other
nine. Fixing it to the one would have broken the majority.

Point at where a value lives rather than copying it. A copy drifts and then
quietly lies. The brand red sat wrong in a memory file for months because it
was written out instead of pointed at. Brand facts live in
`brand/Roy R. Fisher Design System/tokens/` and nowhere else.

Ask how often a rule can fire before you attach work to it. A rule that says
"when this changes, do that" is cheap while the thing changes a few times an
hour. It is ruinous when something starts changing it five times a second. The
photo screen asked the server for the caption price every time the app's note
changed, and then a caption box started changing that note on every keystroke.
On Colleen's machine that is one read across the office network per letter she
types. Both rules were correct on the day each was written.

## The app itself

**It must run on Mark's Windows PC.** On his machine, nothing but Python runs.
No shell script, no Node, no Mac-only call. Every extra thing the app needs is
another thing that can break on his computer and another thing somebody has to
install for him. It has to keep running on Spenser's Mac too.

**Three words, not ten.** Every word on screen earns its place or goes.
Spenser, 2026-09-14: *"DONT USE 10 WORDS WHEN 3 WILL DO"*. A cost was showing
as three stacked lines where one would do, and two sentences said the same
thing about his money in different words. He reads every screen and he is
fast; padding costs him time on every visit, forever. Reassurance is the worst
offender, because it feels kind and it is just noise the tenth time he sees it.
Say it once, in the fewest words that are still true, or do not say it.

**Text fills the box it sits in.** Spenser, 2026-09-17, on the update box:
*"you randomly wrap the text one-third of the way over."* Nothing caps the
width of words. If a line is too long to read, the box is too wide: narrow the
box, never the text. It happened because a line-length habit from print
typography was applied by reflex, hid inside a style borrowed from the
Settings cards, and was checked by reading a rule instead of looking at a
screen. A test now refuses any width in `ch` or `em`.

**Five kinds of thing, and each gets one home.** Spenser's theory, approved
2026-09-14, after a night of fixes that each answered one screenshot and added
up to nothing. Every screen is built against this, not against the last picture
he sent.

1. **What is being made.** A screen that makes a file is named by that file.
   The photographs screen is titled with the document's own name, not the word
   Photos, and shows `file name here.docx` in grey when the name cannot be read
   yet. Under it only the numbers that describe the file.
2. **What shapes it.** The settings that change what comes out. They sit
   together and they look like settings.
3. **What you can do.** The buttons. One place, nothing else in it.
4. **What is happening right now.** One widget, one place, never two at once.
   Progress, the last thing that happened, and anything blocking him. This is
   the home of every message the screen used to scatter. The photographs screen
   could stack eleven separate boxes above his photographs, and on 2026-09-04 he
   asked what happens when three or four pile up. This is the answer.
5. **The content.** His photographs, his files, his list. Everything above gets
   out of their way.

Four rules fall out of it.

**A hint lives on the thing, not as a sentence.** "Drag a photo to reorder it"
goes; the photographs afford dragging.

**A number the app knows exactly is stated exactly.** Sixty photographs at three
to a page is twenty pages, not about twenty.

**What blocks an action is said by the action.** Not in a line above it. The
Build button already says why it is off when he hovers it.

**Two controls doing different jobs do not look the same.** Bands is on or off.
Per page is a value. Today they are identical pills, which is why they read as
noise rather than as two different questions.

**The widget's bottom bar is not a catch-all.** Spenser, 2026-09-18: *"We
need to be careful with this box because I think it's becoming a
catch-all."* The bar answers one question, how he gets to done, and nothing
new goes into it unless something comes out or the new thing goes elsewhere.
Today it holds four things: the `N of M reviewed` pill, which is also the
offer to tick them all once every photograph has words; `Clear captions`,
only while there is a caption to clear; the curved arrow that restores
cleared captions (`Restore cleared captions`), grey until a clear; and the
money, an estimate with a tilde before anything is spent and what was spent
after. `app/tests/test_the_bar_is_not_a_catch_all.py` fails when a fifth
appears, so the trade is made on purpose.

**The photographs screen is the worked example**, and it is saved at
`docs/design/photos-screen.html`. Open it in any browser. It is built from this
app's own stylesheet, so its values are this app's values, and the buttons
along the top put it into every state the real screen can be in. Spenser
approved it on 2026-09-15 after eight rounds of corrections, every one of them
his. When it and a builder's judgement disagree, it wins. It does not delete
itself: the whole of 2026-09-14 was spent recovering a design conversation
that was never written down.

**Blue words go in the lower right. Everywhere, no exceptions.** Spenser's
rule, 2026-09-15, stated in capitals after a round in which three sensible
exceptions were kept and handed back to him as reasoning. A rule with three
exceptions is not a rule. On any row, the things that act sit on the left and
the thing that only shows, explains or backs him out is pushed to the right
hand end. Buttons are not affected. Build it by letting the app's own
`margin-left: auto` on `.linky` stand rather than by adding a class to opt in,
so a link written next month lands in the right place without anybody
remembering to tag it.

**A click leads to a step.** A choice that shapes an action lives inside that
action, asked when he clicks it, never parked on the page beside it. Actions
sit at the top of the screen on the title's row. The content he came to see
starts immediately.

**Test the claim with the right evidence.** Valid synthetic files and temporary
folders may test narrow mechanics such as parsing, error handling, naming,
confinement, and non-overwrite behavior. They prove only that mechanic. They
may not support claims about Mark's real folder structures, documents, layouts,
reports, or workflow. Those claims require the real corpus.

Three external conditions may be stood in for:

- the Anthropic model, so a test run costs nothing, needs no internet, and
  gives the same answer twice
- the answer to "are we on Windows", so drive letters and a drive that fails
  can be tested without a Windows machine
- a fake project folder for the demo-reset tests, so a test of "replace this
  folder" can never be pointed at the real one

Product acceptance and claims about Mark's work run on real folders and real
files.

## Working style

Plan, build, red-team, debrief, then fold what was learned back into these
files. Do not skip the debrief.

Big or hard-to-reverse moves get a question first. Routine work inside an
agreed plan does not.

Each slice of work gets its own branch, so unfinished work can be thrown away
cleanly and the working branch always runs. Once Spenser approves the slice
plan, local commits on that slice branch are allowed as recovery checkpoints.
Nothing is pushed, opened as a pull request, merged, treated as accepted, or
delivered without Spenser seeing the change and saying yes.

While a slice is still being understood there is no plan document, because we
are finding the edges. Once its shape is known, write one.

Write down what he decides on the day he decides it. A decision spoken in a
session lives only in that session. On 2026-09-04 Spenser walked every screen
and marked each click Fine or Not fine. Nobody wrote it down, so the work that
followed has four commits and no document, and every session after it read the
commits and concluded it was a colour pass. His complaint about the Settings
layout was written up as a complaint about red buttons and closed by a colour
rule. Recovering the real list cost an evening on 2026-09-14. It is now in
`docs/THE-WALK-2026-09-04.md`, which does not delete itself.

Every plan destroys itself. A plan is a work list, and a finished work list is
clutter that the next session reads as current. The last task in any plan is to
fold what was learned into these files and then delete the plan. What is worth
keeping is a decision or a measurement, and neither of those lives in a plan.
Plans live in `docs/plans/`; what they leave behind goes to `docs/ROADMAP.md`,
which is the one document meant to grow. A test enforces this, because a rule
nobody is reminded of lasts until the first busy session.

## Approval

After every Builder report, Codex gives Spenser the four-part Product Control
Brief defined below. Recommendations remain proposals until Spenser explicitly
approves them. Codex does not provide the next Builder instruction until
Spenser approves the next action. Any new product behavior, spending,
privacy, file handling, delivery, permission, or scope decision requires
explicit approval. The Builder must separate completed work, proposals, and
decisions needed from Spenser.

## Product Control Brief

After every Builder report, Codex must brief Spenser using these four sections:

1. `What changed`
   - State only completed work.
   - Identify changed files, tests, commits, and verification.
   - Keep proposed work separate from completed work.

2. `User experience`
   - State what the user sees or does differently now.
   - Separate current behavior from planned behavior.
   - Identify frontend effects and backend, data, privacy, security,
     performance, or cost effects.
   - If there is no user-visible or backend impact, explicitly state `None`.

3. `Your decisions`
   - Identify every product decision still requiring Spenser.
   - Include the recommendation and its tradeoff.
   - Silence, prior discussion, technical convenience, and a Builder
     recommendation do not constitute approval.

4. `Next move`
   - State the smallest recommended next action.
   - State the exact approval gate before work continues.

The Builder must provide enough evidence for Codex to produce this brief
without guessing. No material product behavior, spending, privacy, file
handling, delivery, permission, or scope decision may be implemented without
Spenser's explicit approval.

## Not for Mark

`Reset demo` puts the demo job folders back to a known state so the same test
can be run from the beginning over and over. It is Spenser's testing tool. It
only appears on a machine explicitly configured for it, and it comes out of
anything Mark receives.

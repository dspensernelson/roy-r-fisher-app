# How we work on this

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

# How we work on this

Spenser's rules. Edit this file and the rules change. Nothing else governs how
Claude behaves on this project.

## Talking to Spenser

Main point first. Short sentences. Common words. Say what you found, what it
means, and what you recommend. One recommendation, not a survey of options.

He directs the build. He does not work in the code. If he meets a term he does
not recognise, that is a defect in the writing, not a gap in him.

No em dashes, anywhere, ever. Hyphens instead. En dashes are fine; they are
The appraiser's own caption style.

Before asking him to decide about any document, open it and say what is
actually in it. He did not write most of the documents in this repo and should
not have to guess at their contents.

## Files

Never create a markdown file, doc, or note without asking first. This includes
scratch files. When the thing he asked for is text he will read, put it in the
chat.

Never write anything into `Report Examples/`.

Never move, print, or copy a key or a password.

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

## The app itself

**It must run on the appraiser's Windows PC.** Pure Python in the product path. No
Mac-only calls, no absolute paths. It has to keep running on Spenser's Mac too.

**A click leads to a step.** A choice that shapes an action lives inside that
action, asked when he clicks it, never parked on the page beside it. Actions
sit at the top of the screen on the title's row. The content he came to see
starts immediately.

**The app never states a fact it cannot observe.** The output is a signed
appraisal report. A blank costs the appraiser ten seconds. A confident wrong answer
reaches a client and nobody can tell it from his own writing. Name the
tempting unobservable facts in any prompt and forbid them, with the reason.
Verify against real inputs, never mocks. A mock cannot fabricate.

## Working style

Plan, build, red-team, debrief, then fold what was learned back into these
files. Do not skip the debrief.

Big or hard-to-reverse moves get a question first. Routine work inside an
agreed plan does not.

There is deliberately no plan document. We find the edges as we go.

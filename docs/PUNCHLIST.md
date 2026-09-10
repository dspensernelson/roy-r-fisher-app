# Punch list

**Things that are stuck on Spenser.** Not bugs, because nothing is broken. Not
futures, because nobody can build them until he answers. Questions and
decisions, and they leave this file the moment he settles one.

That is a real job for a file, and it is why this is not a drawer for anything
that does not fit elsewhere. If something here is not waiting on him, it is on
the wrong list.

Where the answer goes when he gives one: into `docs/FUTURES.md` if it describes
something to build, into `docs/ROADMAP.md` if it is a decision that outlives the
thing it decided.

---

## Answered on 2026-09-03, kept here until the work lands

**P4. The black window.** Answered. Hidden completely. Spenser, 2026-09-03: *"I
just want the app to open like an app."* He also wants a desktop icon you
double-click, which the installer already makes, so the work is hiding the
console and nothing else. This is B8.

**P5. Moving `Close the app` into the nav bar.** Answered. No belt and
suspenders: it comes out of Settings entirely, moves into the nav bar next to
`Settings`, and gets a confirm step it does not have today. Written out in full
in `docs/FUTURES.md` under F13.

---

## Open

## P2. How far back should the log go?

Spenser's instinct: 24 hours as standard, because problems surface straight
away. He asked for a recommendation and for a way to get more when it is
needed.

**My recommendation, for him to accept or reject.** Keep seven days rather than
one, capped by size so it can never run away. Two reasons. Colleen's whole
session on 2026-09-03, an hour of heavy use, was a few hundred lines, so seven
days is small. And a fault that shows up on a Friday will not be looked at
until Monday, which one day does not survive.

When he reads it remotely, hand him the last 24 hours by default and everything
held on request. That way the common case is short enough to read and the rare
case is still there.

**Not decided. Nothing is built to this yet.**

## P4. Which job produced the 700 KB photographs?

Spenser, 2026-09-10: a document his dad built came out with photographs over
700 KB each. Nobody can look at it until he names the job.

**What is already measured, so nobody measures it twice.** Sixty photographs
from `TEST JOBS` were put through the exact step the build uses, which makes a
JPEG copy capped at 1600 pixels on the longest edge at quality 85. None reached
700 KB. The biggest was 600 KB from a 2400 by 1800 source and the middle of the
pack was 269 KB. Nothing passes through unconverted, so a large result means
either a busy picture or a path nobody has looked at yet.

**Needs the job name from Spenser.** Then the folder can be measured directly
and this becomes a bug or a nothing.

## P3. What does Reset put back?

Spenser, 2026-09-03, thinking aloud and saying so: keep the captions, put
everything else back, maybe the original order, maybe drop anything added. He
asked for ideas or for it to stay parked.

**Parked is right, and here is the hard part.** "Back to the start" has no
single meaning once somebody has added photographs, taken others out, and
captioned some of them. Every version of it destroys something a person might
have meant to keep.

**Three shapes worth arguing about, none of them chosen:**

1. **Forget what the app decided, keep what a person typed.** Captions and
   ticks survive. Order goes back to capture order. Anything added stays but
   returns to unassigned. Nothing on disk is touched.
2. **Forget everything except captions.** Order, ticks, what is in and out, all
   go back to a fresh read of the folder. Captions are matched back by
   filename.
3. **Forget the app's own note entirely and start again**, which is what
   deleting `photo-manifest.json` by hand did on 2026-09-03, and it is why this
   question exists.

Whichever way it goes, `Clear captions` keeps meaning exactly what it says. It
is not the same button and must not quietly become one.

**Needs Spenser. Do not build it.**

# Prompt for the builder

Copy everything below the line into your coding agent (Claude Code, Cursor, or
similar) at the start of the session. It assumes the design system folder has
been placed inside or alongside the repo.

---

You are working on the Roy R. Fisher appraisal assembly app — a local React +
FastAPI application that turns a job folder into a formal commercial appraisal
report. It runs offline on one Windows machine for one user: Mark, a commercial
appraiser who has produced these reports in Word for decades and is not a
software user by inclination.

A design system for this app exists. Before you write any code, read these three
files in full:

1. `BUILD.md` — the adoption order, the full CSS class vocabulary, the
   non-negotiable rules, and what is still an open product decision.
2. `readme.md` — the design guide. Note its three-tier structure: Tier 1 (brand
   facts) is binding, Tier 2 (the kit) is take-it-or-leave-it, Tier 3 (the app
   proposal) is an argument you are allowed to win.
3. `ui_kits/appraisal-app/PROPOSAL.md` — the product decisions embodied in the
   click-through, each with the reasoning and an explicit "overrule this if…".

Then open `ui_kits/appraisal-app/index.html` in a browser. It is plain HTML and
vanilla JS with no build step and no network calls — it shows all seven screens
working. That file is the reference for what things should look and behave like.

## How to treat the design system

**It is a kit, not a specification.** It has deliberately no opinion on product
behaviour: what a screen is for, how work is ordered, what the app knows or
stores, folder and section rules, when to call the model, routing, or state.
Those are yours. If something in the UI kit or a `.prompt.md` reads like a
product rule, it is describing the proposal, not constraining you.

**Take one level of buy-in and stay there.** Either use the CSS custom
properties only, or use the `rrf-*` class layer with your own markup, or import
the React components in `components/*/`. The class layer is the recommended
middle: it survives any refactor of component structure, needs no build step,
and is what the click-through itself uses. Do not mix levels arbitrarily.

**Never reproduce a raw value that has a token.** If you find yourself typing a
hex code, a px size, a radius or a duration, there is a token for it. The one
exception is a genuinely new value, in which case add it to `tokens/` with a
comment saying why, rather than inlining it.

## Rules that must hold everywhere, now and in future work

These are short because everything else is negotiable. Apply them to every
screen you touch and every screen you add:

1. **Brand red is `#8C0C04`.** Never `#782028` (the old app's guess), `#7A222E`
   or `#702930` (degraded website variants). If you find any of those in the
   codebase, replace them.
2. **Red appears at most twice on a screen**: the 3px letterhead band at the top
   of the window, and the primary button. A third red element means something
   else must give it up. Red is identity and the single most likely action —
   never a generic "interactive" colour.
3. **Two surfaces only.** Eggshell `--surface-page` is the page; white paper is
   everything on it — rows, cards, panels, fields, photo tiles, messages,
   overlays. Charcoal `#343538` is the crumb bar and nothing else. **Any colour
   that reads well on charcoal should be assumed wrong on paper until measured**
   — four separate defects in this system came from exactly that assumption.
4. **These pairings are retired and must not come back:**
   - `--link` (`#1B6C99`) is for paper. `--link-on-dark` (`#248CC8`) is for dark
     grounds. Never cross them.
   - `--text-secondary` on `--quiet-bg` is 4.33:1. Use `--ink-on-quiet`.
   - `--ink-faint` no longer exists. Placeholders use `--text-placeholder`;
     quiet glyphs use `--text-secondary`.
5. **Everything meets WCAG AA on the ground it actually sits on** — including
   placeholder text, `::before`/`::after` content, and SVG glyphs at the 3:1
   non-text threshold. If you introduce a colour pair, measure it against the
   computed background, not the one you assume is behind it. Set placeholder
   colour explicitly on every input; left to the browser it inherits a UA
   default that varies per browser.
6. **Never redraw the mark.** Use `assets/logo/rrf-mark.svg` or the raster
   masters. It is three columns with an angled cut on the taller centre one; the
   old app approximated it with plain bars in the wrong red.
7. **Colour is never the only signal.** State lines and banners carry a glyph as
   well as a colour; what tells the user something is pressable is always the
   word — *Open*, *Open folder*, *Change sections* — never a rule or a hue alone.
8. **No emoji, anywhere.**

## How the app should talk

The copy is the strongest thing the current app has. Preserve it literally, and
write new strings the same way:

- Always *you*, never *we*, never the app naming itself. Statements about what
  will happen, not commands: "Nothing is made until you press the button at the
  bottom."
- Sentence case everywhere. Uppercase only in tracked micro-labels
  (`WHAT HAS ARRIVED`, `NEEDED TO START`) and the wordmark. Never Title Case.
- Buttons are verb phrases naming the outcome: "Make the job", "Build photo
  pages", "Save these sections". Never "Submit", "OK", "Continue", "Confirm".
- Labels are the words Mark would say: "Kind of property", "Effective date of
  value", "Office file number". Never schema names.
- Errors say what to do, never what failed: "Could not reach the app's server.
  Close this tab and start the app again." No codes, no "Something went wrong."
- Results say what was made **and what was not touched**: "Done. **Photo
  Pages.docx** was created in this job's Photos folder. Nothing was overwritten."
  Reassurance about his originals is part of the copy, not a footnote.
- Limits are admitted once, quietly, above the list — not stamped on every row.
  Unbuilt features are shown with a "Not built yet" tag rather than hidden.
- Counts are plain and singular-aware. Ellipses mark work in progress:
  "Writing captions…".
- Use the domain's own terms exactly — *engagement letter*, *assessor PRC*,
  *salient facts*, *highest and best use* — and never simplify them.

## Two interaction principles the app already gets right

Keep both. They are the reason the app feels like an instrument rather than a
form:

1. **A click leads to a step.** Choices live inside the action they shape. When
   Mark presses *Suggest captions*, he is asked how captions should read right
   there, over his own photos, shown both ways. Nothing is parked in a settings
   panel.
2. **Actions sit at the top; content starts immediately.** No hero areas, no
   preamble, no empty banner rows. The screen title and its actions share one
   line, and the work begins directly beneath.

## Known bugs to fix early

Both are in the current app, both are pure wins, neither involves a design
decision:

- **Photo captions render at 13.33px monospace.** `app/web/src/brand.css`
  declares `font: 14px/1.45 inherit`; `inherit` is invalid inside the `font`
  shorthand, so the entire declaration is dropped and the browser falls back to
  its default. Set the properties individually — `.rrf-phototile__caption` does.
- **Captions are clipped.** The field is `overflow: hidden` with a fixed
  min-height and pre-filled captions never trigger auto-grow. When you fix it:
  measure `scrollHeight` only when the element is **visible** and after fonts
  have settled. A hidden element reports `scrollHeight: 0`, so a caption sized
  at mount is sized against nothing — this is subtle and it will bite you.

Also delete `app/web/src/brand.css` once `styles.css` is linked. Everything in
it is superseded and its red is wrong.

## Suggested order

1. Link `styles.css`; delete `brand.css`; add `<div class="rrf-topline"></div>`
   as the first element in the body.
2. Fix the two caption bugs.
3. Replace the inline masthead SVG with `assets/logo/rrf-mark.svg`.
4. Convert **Settings** first — smallest screen, real state machine
   (off → checking → on), exercises about half the vocabulary.
5. Then **Photos** — the only section that builds, and where Mark spends time.
6. Then the rest. Leave the **Job** screen until last; it still has open product
   questions (below).

## Open questions — decide these with the designer, not alone

`PROPOSAL.md` covers each in full. Do not treat any of them as settled:

- **The job screen as a worklist**, ordered by what Mark can do without waiting
  on anyone, with every gap becoming a task that names the sections waiting on
  it. That last part requires the section engine to map inputs → sections; if it
  can't, the rows still work with the second line dropped.
- **Nothing claims who is blocking.** The app reads folders; it does not know
  the rent roll is with the owner. If you build a way for Mark to mark a request
  as sent, a "waiting on someone else" group becomes honest and should return.
- **"Which way it faces" needs an approval path.** If the app infers direction,
  Mark must be able to correct it — a per-photo confirm, which is a different
  overlay from the style chooser. If he supplies it, it is a field, not a
  caption style. It may also apply only to roads and right-of-way work, in which
  case it belongs in the engagement matrix.
- **Folder counts per engagement type** (nine for a tax appeal, eleven for a
  full appraisal) are a guess. The real matrix is in `shop/data/`.

## When you add something the system doesn't cover

Expected and fine. In order of preference:

1. Compose it from existing classes.
2. If it needs a new class, add it to `components/rrf-components.css` using
   existing tokens, with a one-line comment saying what it is for.
3. If it needs a genuinely new value, add the token to `tokens/` with the
   measured contrast ratio in a comment where it is a text colour.
4. Tell the designer what you added, so the specimen cards and the readme stay
   true. Documentation drift in this system has caused real defects — a card
   that still shows a retired pattern hides the fact that the pattern is gone.

Do not invent new primitives that the app has no use for. There is no Toast, no
Tabs, no Tooltip, no Avatar, and no modal beyond the one `Sheet`, because the
product has none.

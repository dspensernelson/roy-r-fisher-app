# Start here — adopting this system in the app

For whoever is writing the code. This is the shortest path from the current
`RRF/app` to something running on this design system. It assumes the existing
React + FastAPI app in `app/web/src/` and `app/server/`.

Read `readme.md` for *why*. This file is *how*, in order.

**Using a coding agent?** Paste `BUILDER_PROMPT.md` into it at the start of the
session — it carries the standing rules, the voice, and the open questions in a
form the agent can hold across a long build.

---

## What you are adopting

**One stylesheet.** Everything visual in this system is plain CSS custom
properties plus a class layer. No framework, no build step, no npm package, no
network. If you take nothing else, take this.

```
styles.css                      → @imports everything below
  tokens/colors.css             114 custom properties
  tokens/typography.css
  tokens/spacing.css
  tokens/shape.css
  tokens/motion.css
  tokens/base.css               reset, body type, links, :focus-visible
  components/rrf-components.css the rrf-* class layer
assets/logo/                    mark (raster + vector), lockup, letterhead
assets/icons/sprite.svg         8 glyphs
```

**Three levels of buy-in — pick one, they don't depend on each other.**

1. **Tokens only.** Link `styles.css`, use `var(--*)` in your own CSS. Lowest
   commitment; still gets you the measured brand and a real scale.
2. **The class layer.** Write your own markup, put `rrf-*` classes on it. This
   is what the UI kit does and what I'd suggest — it survives any refactor of
   your component structure.
3. **The React components** in `components/*/`. Only worth it if you want the
   props contracts; they're plain JSX with no dependencies but React.

---

## First session, in order

### 1. Get the stylesheet in (30 minutes)

Copy `styles.css`, `tokens/`, `components/rrf-components.css`, `assets/logo/`
and `assets/icons/` into the web app. Link `styles.css` once, at the top of
`index.html`. Delete `app/web/src/brand.css` — everything in it is superseded,
and its `--red: #782028` is the wrong red.

Check one thing before moving on: the page ground should be `#FAF8F4` and the
body font should resolve to Segoe UI on Mark's machine.

### 2. Fix the two confirmed bugs (20 minutes)

These are in the current app and are worth doing first because they're pure
wins with no design decisions attached:

- **Photo captions render at 13.33px monospace.** `app/web/src/brand.css`
  declares `font: 14px/1.45 inherit` — `inherit` is not valid inside the `font`
  shorthand, so the whole declaration is dropped and the browser falls back to
  its default. Use `.rrf-phototile__caption`, which sets the properties
  individually.
- **Captions are clipped.** The field is `overflow: hidden` with a fixed
  min-height and pre-filled captions never trigger the auto-grow. The fix is in
  `PhotoTile.jsx` — and note the subtlety that cost me an hour: measure
  `scrollHeight` **when the screen is visible and after fonts settle**. A hidden
  element reports `scrollHeight: 0`, so a caption sized at mount is sized
  against nothing.

### 3. Replace the masthead SVG (10 minutes)

The current inline SVG hardcodes the wrong red three times and draws three plain
bars, missing the angled cut. Use `assets/logo/rrf-mark.svg` (or the `.png`).
Add `<div class="rrf-topline"></div>` as the first element in the body — that
3px red band is the system's one piece of decoration.

### 4. Convert one screen, not all of them (half a day)

Do **Settings** first. It is the smallest, it has a real state machine
(off → checking → on), and it exercises `SettingCard`, `Lamp`, `Field`,
`Button`, `LinkButton`, `Banner` and `Working` — about half the vocabulary — in
one screen you can hold in your head.

Then **Photos**, because it is the only section that builds and it is where
Mark spends his time.

Leave the Job screen until last: it is the one with real product decisions still
open (see below).

---

## The class vocabulary

Enough to write markup without reading the CSS.

| Class | What it is |
| --- | --- |
| `rrf-topline` | the 3px red letterhead band, first element on the page |
| `rrf-masthead`, `rrf-wordmark`, `rrf-tagline` | brand row |
| `rrf-crumbbar` / `rrf-crumbbar__inner` / `rrf-crumb` | the charcoal bar |
| `rrf-frame` | the 1200px content frame |
| `rrf-screenhead` + `rrf-title` / `rrf-sub` / `rrf-actionrow` | title row with its actions |
| `rrf-bandhead` + `__title` / `__note` | ruled uppercase heading |
| `rrf-bands` | the 1.45fr / 1fr split |
| `rrf-btn` + `--primary` / `--secondary` / `--quiet` / `--sm` | buttons |
| `rrf-link` + `--body` | link-styled button |
| `rrf-seg` / `rrf-seg__btn.is-on` / `rrf-seg__flag` | segmented control |
| `rrf-chip` + `--live` / `--quiet` / `--done` / `--needs` | row-end pill |
| `rrf-lamp` + `--on` / `--off` / `--busy` | word-based state |
| `rrf-cards` / `rrf-jobcard` + `__city` `__addr` `__meta` `__next` `__far` `__bar` | job grid |
| `rrf-roads` / `rrf-roadcard` / `rrf-tag-soon` | route choice |
| `rrf-panel` + `__label` / `__note` | grouped fields |
| `rrf-settingcard` + `__head` / `__body` / `__fine` | one setting |
| `rrf-emptynote` | empty state |
| `rrf-fields` / `rrf-field` + `__label` `__input` `__hint`, `.is-derived` `.is-error` `.is-mono` | forms |
| `rrf-checklist` / `rrf-check` `.is-off` | checklist |
| `rrf-dropzone` `.is-over` | drop target |
| `rrf-banner` + `--done` / `--error` / `--warn` / `--note` | messages |
| `rrf-working` / `rrf-sweep` | the one animation |
| `rrf-draghint` | drag pill |
| `rrf-folder` + `__top` `__name` `__count` `__line--has/--needs/--quiet` | folder row |
| `rrf-sectionrow` + `--live` / `--soon` / `--done`, `__num` `__name` `__state--needs/--has` | section row |
| `rrf-worklist` / `rrf-task` + `--next` / `--done`, `__name` `__why` | worklist |
| `rrf-subhead`, `rrf-progress` | group heading, completeness line |
| `rrf-photogrid` / `rrf-phototile` + `__caption` | photos |
| `rrf-pagepreview` + `__photo` `__caption` | the printed-page facsimile |
| `rrf-sheet-back` / `rrf-sheet` + `__title` `__sub` `__foot` `__keep` | the overlay |
| `rrf-icon` + `--lg` / `--quiet` / `--has` / `--needs` | glyph wrapper |

**Icons:** inline `assets/icons/sprite.svg` into the page and reference
`<svg class="rrf-icon"><use href="#folder"></use></svg>`. Inlining matters —
`<use>` pointing at an external file fails under `file://` and adds a request
you don't need. Glyphs: `folder`, `image`, `file-text`, `grip-vertical`,
`check`, `triangle-alert`, `chevron-right`, `x`.

---

## Five rules that are not negotiable

Everything else in this system is a suggestion. These five are the ones that
will visibly break the brand or the accessibility floor if you drift:

1. **Brand red is `#8C0C04`.** Not `#782028`, `#7A222E` or `#702930`.
2. **Red appears twice per screen at most**: the letterhead band, and the
   primary button. Never a third time.
3. **Do not put `--link` on charcoal, or `--link-on-dark` on paper.** They are
   different values because those grounds are different.
4. **Do not pair `--text-secondary` with `--quiet-bg`** — 4.33:1, under AA. Use
   `--ink-on-quiet`.
5. **Never redraw the mark.** Use the files in `assets/logo/`.

Everything in the system is currently measured at WCAG AA or better, including
placeholders and generated content. If you add a colour pair, measure it.

---

## What is still an open product decision

These are in `ui_kits/appraisal-app/PROPOSAL.md` with the reasoning and an
"overrule this if…" line each. Short version of what is *not* settled:

- **The job screen is a worklist.** Ordered by what Mark can do without waiting
  on anyone. Every gap becomes a task naming the sections that wait on it — this
  requires the section engine to map inputs → sections. If it can't, the rows
  still work with the second line dropped.
- **Nothing claims who is holding something up.** The app reads folders; it does
  not know the rent roll is with the owner. If you give Mark a way to mark a
  request as sent, a "waiting on someone" group becomes honest and should
  come back.
- **"Which way it faces" needs an approval path.** If the app infers direction,
  Mark must be able to correct it — that's a per-photo confirm, a different
  overlay from the style chooser. If he supplies it, it's a field. Unresolved.
  It may also only apply to roads and right-of-way work, in which case it
  belongs in the engagement matrix, not the caption chooser.
- **Folder counts per engagement type** (nine for a tax appeal, eleven for a
  full appraisal) are a guess. The real matrix is in `shop/data/`.

---

## Where things are

| Path | What |
| --- | --- |
| `ui_kits/appraisal-app/index.html` | the click-through — all seven screens, vanilla JS, opens offline |
| `ui_kits/appraisal-app/PROPOSAL.md` | product decisions + reasoning, non-binding |
| `ui_kits/appraisal-app/*.jsx` | the same screens using the React components |
| `components/*/` | 33 components, each with `.d.ts` and `.prompt.md` |
| `guidelines/*.card.html` | foundation specimens |
| `guidelines/*-options/` | the alternatives that were considered and rejected, kept as a record |
| `readme.md` | the design guide |

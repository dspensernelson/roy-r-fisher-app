# Roy R. Fisher — design system

Roy R. Fisher, Inc. is a commercial real estate appraisal firm in Davenport, Iowa, founded by Roy R. Fisher, Sr. (1890–1978). Its tagline, italic under the wordmark on every letterhead, is *"The Established Commercial Valuation Experts."* The firm's product is a formal appraisal report: Times New Roman, double-ruled boxes, all-caps headings, 20–90 body pages, delivered as a Word document and a PDF.

This system covers the firm's one piece of software: a local app that assembles that report out of a job folder. It runs offline on a Windows machine for a single user — Mark, an appraiser who has produced these reports in Word for decades.

The app is a tool he works in. **It produces the document; it does not imitate it.** Nothing on screen is set in Times except the facsimile of a printed page.

---

## How to use this without fighting it

This system is in **three tiers**, and only the first is binding. Read the tier before you take an argument from it.

| Tier | What it is | How binding |
| --- | --- | --- |
| **1 — Brand facts** | colours, logo files, type stacks, the letterhead rule | **Adopt.** These are measured from delivered work, not designed here. Changing them makes it not-RRF. |
| **2 — A kit to build from** | tokens, CSS classes, React components | **Use what helps.** Take one level or all three. Nothing here requires anything else here. |
| **3 — One worked proposal** | the app UI kit and its screens | **Argue with it.** It is an illustration of the tiers above, not a spec. |

**Three levels of buy-in, and you pick one.** Link `styles.css` and use the custom properties only. Or use the `rrf-` CSS classes and write your own markup. Or import the React components. Each level works alone; none assumes a framework, a build step, or a network.

**Writing the code? Go to `BUILD.md`** — it has the adoption order, the full class vocabulary, the five non-negotiable rules, and the list of product decisions still open.

### What this system deliberately does not decide

Product behaviour is the builder's, not the design system's. This system has no opinion on — and should not be cited about — any of the following:

- what a screen is *for*, or what belongs on it
- how work is ordered, grouped, or prioritised for the user
- what the app knows, infers, or stores
- folder structure, file naming, section rules, engagement types
- when to call the model, what to send it, what to do with the answer
- routing, state, persistence, or error recovery

If something in `ui_kits/` or a `.prompt.md` reads like a product rule, it is describing **the proposal**, not constraining the build. The Tier 1 list below is the whole of what this system asks you to honour.

---

## Tier 1 — Brand facts

Everything here was measured from the delivered report corpus or the firm's own assets. This is the short list worth holding the line on.

**Colour.** Brand red `#8C0C04` (dominant across 13 logo assets in six job folders), hover `#B30F05`, ink `#231F20` — the logo's warm near-black, not pure black. Not `#782028` (the old app's guess), not `#7A222E` or `#702930` (degraded website variants).

**Ground.** Eggshell `#FAF8F4` page, white `#FFFFFF` paper, hairline `#E3E0D8`. Warm, not neutral grey.

**Link blue `#1B6C99`** — 5.02:1 on white, 4.83:1 on eggshell, hover `#14536F` at 7.35:1. This carries every secondary action: the *Open* chip, Cancel, Add photos, Change sections. The old app's `#248CC8` read at 4.6:1 because it sat on charcoal; on paper it is only 3.5:1, below AA, so it survives as `--link-on-dark` for dark grounds only. **Do not put `--link` on charcoal or `--link-on-dark` on paper.**

**Type.** No webfonts — the app runs offline, so both stacks are resident faces. Sans leads with **Segoe UI** (native on Mark's machine, warmer than Helvetica, steadier in long lists), falling back to Helvetica Neue and Arial. Serif is Georgia / Times New Roman, used for the wordmark and for anything standing in for the printed page.

**The mark.** `assets/logo/` — three columns with an angled cut on the taller centre one. Raster masters plus `rrf-mark.svg`, traced by measuring the raster's pixel edges (red column x26–54, apex y2, cut full-width by y26, foot y214; dark columns 20 wide, cut over 22px, foot y195). **The trace still wants sign-off before it goes on anything printed.** Never redraw the mark from memory or approximate it with plain bars; knock it out to white on charcoal rather than tinting it.

**The letterhead rule.** A 3px brand-red band across the very top of the window, the way it runs across the printed letterhead. This is the app's one piece of decoration, chosen over serif titles and over repeating the mark, because three signatures on one screen is how "bespoke" becomes overdone.

**Every text colour in the system meets WCAG AA on the ground it is used on** — checked by measuring, in all 35 rendered pages of this project, every text node, every `::placeholder`, every `::before`/`::after` with generated text, and every SVG glyph (against the 3:1 non-text threshold), each against the background actually computed behind it. Not by inspection. Ratios are recorded beside the tokens in `tokens/colors.css`. The app has one user, on a Windows machine, who is not a software user by inclination; legibility is not a nicety here.

Two pairings are retired and must not be reintroduced, because both were derived against charcoal and are illegible on paper:

- `--text-secondary` on `--quiet-bg` (4.33:1) — use `--ink-on-quiet`.
- `--link` (`#248CC8`) anywhere on paper (3.5:1) — that value survives only as `--link-on-dark`.
- `--ink-faint` (`#93938F`) is **deleted**. It read 6.4:1 on charcoal and 3.08:1 on paper, and was still colouring placeholder text. Use `--text-placeholder` for placeholders and `--text-secondary` for quiet glyphs.

Placeholders are set explicitly on every input. Left to the browser they inherit a UA default that differs per browser and happens to pass only by luck.

**No emoji, anywhere.**

---

## Tier 2 — The kit

### Tokens

`styles.css` is the entry point and imports everything. 114 custom properties, all on `:root`.

| File | What it holds |
| --- | --- |
| `tokens/colors.css` | brand, ground, charcoal, text, state, semantic aliases |
| `tokens/typography.css` | the two stacks, an 8-step scale (11 → 28), tracking, measures |
| `tokens/spacing.css` | a 4px grid with one 2px hair step, layout widths |
| `tokens/shape.css` | 3 radii and a pill, borders, rules, 3 shadows, focus |
| `tokens/motion.css` | durations, the sweep and fade keyframes, reduced motion |
| `tokens/base.css` | reset, body type, link colours, `:focus-visible` |

These replace what the old app had: 15 font sizes (including 10.5, 11.5, 12.5, 13.5), 22 spacing values, 7 radii, and 13 hardcoded hex values outside the token block.

**State colours come in pairs** because rows live on paper and panels on charcoal: pale `--has` / `--needs` for dark grounds, `--has-ink` / `--needs-ink` for light. Use the aliases `--text-has` and `--text-needs` and the right one applies. A missing input is amber, never red — nothing is wrong yet.

### CSS classes

`components/rrf-components.css` — every class the components use, prefixed `rrf-`. Usable with no React at all; the UI kit is built this way.

### React components

30 components, each with a sibling `.d.ts` props contract and a `.prompt.md` usage note. Import React only; style via the custom properties; no npm packages.

**`brand/`** — `BrandMark`, `Masthead`
**`layout/`** — `AppShell`, `CrumbBar`, `ScreenHead`, `BandHead`, `Bands`
**`actions/`** — `Button`, `LinkButton`, `SegmentedControl`, `Chip`, `Lamp`
**`surfaces/`** — `JobCard`, `NewJobCard`, `RoadCard`, `Panel`, `SettingCard`, `EmptyNote`
**`forms/`** — `Field`, `Checklist`, `DropZone`
**`feedback/`** — `Banner`, `Working`, `DragHint`
**`job/`** — `TaskRow`, `Worklist`, `Progress`, `FolderCard`, `SectionRow`
**`photos/`** — `PhotoGrid`, `PhotoTile`, `PagePreview`
**`overlay/`** — `Sheet`

**Some of these are shaped by the proposal, not by the brand.** `TaskRow`, `Worklist`, `Progress`, `FolderCard`, `SectionRow`, and `JobCard`'s `next`/`ready`/`total` props all assume the job screen works the way Tier 3 suggests. If the builder lands somewhere else, **delete them** — they cost nothing to drop, and the rest of the kit does not depend on them. The neutral set is `Button`, `LinkButton`, `Field`, `Checklist`, `Chip`, `Lamp`, `SegmentedControl`, `Banner`, `Working`, `Panel`, `SettingCard`, `EmptyNote`, `DropZone`, `Sheet`, `PhotoGrid`, `PhotoTile`, and the brand and layout groups.

Two components exist to prevent specific bugs and are worth keeping either way:

- **`PhotoTile`** — the old app declared `font: 14px/1.45 inherit`, which is invalid, so the whole declaration dropped and captions fell back to the browser's 13.33px monospace; `overflow: hidden` then clipped them. This component grows to fit and never uses the `font` shorthand.
- **`Field`** — carries label, hint, error and disabled in one place, so those states stop being improvised per screen.

### Icons

Eight glyphs in `assets/icons/` (individually and as `sprite.svg`): `folder`, `image`, `file-text`, `grip-vertical`, `check`, `triangle-alert`, `chevron-right`, `x`.

**Flagged substitution:** these are **Lucide** (ISC), stroke reduced from 2 to 1.75 for 16px use. The firm has no icon set of its own, so this is a nearest match rather than a brand asset — worth replacing if one is ever commissioned. The old app had no icons at all and carried affordance in words; that still holds, so a glyph sits beside words at 16px in a row or 20px beside a task, and there are no icon-only buttons. Inline the sprite into standalone pages so `<use>` resolves with no network.

Unicode is used sparingly: `›` (U+203A) as the crumb separator, `+` in "+ New job", and proper curly quotes and dashes in copy.

---

## Visual foundations

The look, described so you can extend it — not a checklist to pass.

**Surfaces.** Two, and only two. Eggshell `#FAF8F4` is the page; white paper is everything on it — rows, cards, panels, fields, photo tiles, messages, the overlay. Charcoal `#343538` survives in exactly one place, the crumb bar, and is not a working surface. Any value that reads well on charcoal should be assumed wrong on paper until measured; four separate defects in this system came from exactly that assumption.

**Rules, not decoration.** Below the letterhead band, rules mark identity and selection — never affordance. A 3px red rule on top of a card is the firm's line (*this belongs to us*). A 4px red rule on the left marks *one* thing — the next task, or the row that opens today — never six at once, which turns the rule into wallpaper. A 2px grey rule under an uppercase label heads a band of rows. 1.5px dashed means nothing here yet. What says something can be pressed is always the word: *Open*, *Open folder*, *Change sections*.

**Cards.** Flat rectangles at 6px radius, separated by a hairline rather than by depth. Three shadows exist in total: `--shadow-raised` (the segmented control's selected pill), `--shadow-float` (the drag pill), `--shadow-sheet` (the overlay). Nothing else casts one.

**Backgrounds.** Flat colour. No gradients, patterns, textures, or hero imagery.

**Imagery.** Inspection photography: daylight, straight-on, unedited, 4:3, cover-cropped, 4px radius. Warm and plain because it is evidence — no filters, duotone, grain, or scrims.

**Hover.** Charcoal lightens a step (`#343538` → `#3E3F43`); the red button goes *lighter*, not darker (`#B30F05`, 7.03:1); paper cards gain the raised shadow and a stronger border; links underline. No opacity fades, no scaling.

**Press.** Primary darkens to `#6E0903` and drops 1px. No ripples, no bounce.

**Disabled.** 45% opacity, default cursor — the button stays visible and labelled, because a hidden action is a mystery.

**Focus.** 2px `#248CC8` outline at 1px offset, on everything interactive, never removed.

**Motion.** One animation: the 1.15s indeterminate sweep that says the machine is working. Hover and press at 140ms, the overlay fade at 220ms, `cubic-bezier(0.2,0,0.2,1)`. Nothing bounces or slides; progress is never faked as determinate; reduced motion drops the transitions.

**Transparency.** Once, for the overlay scrim `rgba(35,31,32,0.55)`. No blur, no frosted chrome.

**Layout.** A 1200px frame with 24px gutters, and a 62ch maximum measure on paragraphs. The 1.45fr / 1fr split is a measured ratio for two columns of wrapping text, not a house grid — use it where it fits and ignore it where it does not.

---

## Content fundamentals

The app talks the way a careful colleague talks. This voice is the strongest thing the current app has, and it is preserved literally — it is also the cheapest tier to adopt, since it costs nothing structurally.

**Always *you*, never *we*.** Statements about what will happen, not instructions: "Nothing is made until you press the button at the bottom."

**Sentence case everywhere** — buttons, headings, labels, chips. Uppercase only in tracked micro-labels (`WHAT HAS ARRIVED`, `NEEDED TO START`) and the wordmark. No Title Case.

**Buttons are verb phrases** naming the outcome: "Make the job", "Build photo pages", "Save these sections", "Use this style". Not "Submit", "OK", "Continue", "Confirm".

**Labels are the words he would say**: "Kind of property", "Effective date of value", "Office file number", "Paste your key" — not schema names.

**Errors say what to do, not what failed.** "Could not reach the app's server. Close this tab and start the app again." No codes, no "Something went wrong."

**Results say what was made and what was not touched.** "Done. **Photo Pages.docx** was created in this job's Photos folder. Nothing was overwritten." Reassurance about his originals is part of the copy: "your originals stay untouched."

**Limits are admitted once**, quietly, above the list — not stamped on every row. Unbuilt routes are shown with a *Not built yet* tag rather than hidden.

**Uncertainty is stated with its evidence.** "We have only one finished report of this kind on file, so this list is a starting point rather than the firm's standard." (The one place *we* appears — the firm about its own records.)

**Counts are plain and singular-aware**: "18 photos, about 6 pages", "1 section checked". Ellipses mark work in progress: "Writing captions…".

**No emoji, no exclamation marks, no jokes, no marketing adjectives.** The domain's own terms are used exactly — *engagement letter*, *assessor PRC*, *salient facts*, *highest and best use* — and never simplified.

---

## Tier 3 — The proposal

`ui_kits/appraisal-app/` is a click-through of one way the app could work: seven screens, plain HTML and vanilla JS, no framework and no CDN, so it opens offline anywhere.

**It is an illustration, not a specification.** The product decisions it embodies — and the reasoning behind each — are written down separately in `ui_kits/appraisal-app/PROPOSAL.md`, precisely so they can be overruled without anyone having to unpick the design system to do it.

---

## Sources this was built from

- **Attached codebase `RRF/`** (read-only, mounted locally):
  - `app/web/src/` — the working React app: `App.jsx`, `brand.css`, and six screens (`JobsPortal`, `NewJob`, `JobHome`, `PhotosScreen`, `SectionPicker`, `Settings`).
  - `app/server/` — FastAPI backend (`jobs`, `scan`, `sections`, `photos`, `captions`, `brief`, `settings`); the source of the app's real vocabulary.
  - `brand/BRIEF.md` — the design brief, including the measured brand colours.
  - `brand/logo/`, `brand/logo-website-variant/` — all logo raster assets.
  - `brand/current-app/` — ten HTML captures of the pre-system screens.
  - `shop/data/` — the engagement matrix, section rulebook, donor ledger and data-source table.
- **No Figma file, no repository, no design tokens existed.** The type scale, spacing grid, radii and state set are new; the colours and assets are measured.

## Index

| Path | What it is |
| --- | --- |
| `BUILDER_PROMPT.md` | **paste this into the coding agent** — the standing rules, voice, and open questions |
| `BUILD.md` | **start here if you are writing the code** — what to copy, what to change, in order |
| `styles.css` | the single entry point — imports every token file and the component CSS |
| `tokens/` | the six token files |
| `components/rrf-components.css` | all component classes (`rrf-` prefix) |
| `components/*/` | 30 React components, each with `.d.ts` and `.prompt.md` |
| `guidelines/*.card.html` | foundation specimen cards (Colors, Type, Spacing, Brand) |
| `guidelines/typeface-options/` | the three typeface directions as the same screen; **Segoe UI was chosen** |
| `assets/logo/`, `assets/logo-website-variant/`, `assets/photography/`, `assets/icons/` | brand assets |
| `ui_kits/appraisal-app/index.html` | the click-through proposal |
| `ui_kits/appraisal-app/PROPOSAL.md` | the product decisions it embodies, and why — non-binding |
| `ui_kits/appraisal-app/*.jsx` | the same screens composed from the React components, for a project with a build step |
| `templates/app-screen/` | a starting frame for a new app screen |
| `thumbnail.html` | the homepage tile |
| `SKILL.md` | Agent Skills entry point |

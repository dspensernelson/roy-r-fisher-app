# RRF app: brief for Claude Design

## Read this first

The screens in `current-app/` are **the current state, not the target**. They were built fast to prove the workflow, and they have no design direction behind them. Treat them as evidence of what the app must be able to do, not as a design to preserve or match.

You are expected to improve on them substantially. The only things below that are fixed are the brand facts and the domain constraints. Everything about layout, hierarchy, component design, and visual language is open.

## Who uses this

One person: Mark, a commercial real estate appraiser at Roy R. Fisher in Davenport, Iowa. He is not a software user by inclination. He runs this on a Windows machine to assemble appraisal reports he has been producing in Word for decades.

The app is a **tool he works in**. Its output is a formal Times New Roman appraisal document with double-ruled boxes and all-caps headings. The app should not imitate that document. It should feel like a clean, calm instrument that produces it.

Two principles the app already gets right and should keep:

1. **A click leads to a step.** Choices live inside the action they shape, not parked in a settings panel. When Mark clicks the thing, he is asked about the thing.
2. **Actions sit at the top, content starts immediately.** No hero areas, no preamble.

## Brand facts (fixed, measured)

Sampled across the delivered report corpus, not chosen:

| Token | Value | Notes |
|---|---|---|
| Brand red | `#8C0C04` | dominant in 13 logo assets across 6 job folders, at 4 resolutions |
| Ink | `#231F20` | the warm near-black of the logo columns, not pure black |
| Brand red hover | `#B30F05` | brand hue at L 36%, 7.03:1 on white |
| Label accent on dark | `#E2928D` | 5.10:1 on `#343538`, passes AA |

Note: the current code uses `#782028`, which is wrong. The website's logo (`#7A222E`) and its button widget (`#702930`) are degraded or incidental variants. The delivered reports are the source of truth.

Existing surface colors that are working and worth keeping unless you have a reason: eggshell ground `#FAF8F4`, charcoal card `#343538`, link blue `#248CC8`.

**Assets** are in `logo/`: the master letterhead at 2474x418, the 466px lockup, the isolated mark and wordmark, transparent versions of each. `logo-website-variant/` is the lower-resolution website logo, kept separate so it is not mistaken for canonical. There is **no vector anywhere**; the mark is three columns with an angled cut on the taller center one, and it redraws cleanly if you want to.

The tagline is "The Established Commercial Valuation Experts". The firm dates to founder Roy R. Fisher, Sr., 1890 to 1978.

## What the app has to do

Six screens, captured in `current-app/` as self-contained HTML you can open and inspect:

| File | Screen | What it is for |
|---|---|---|
| `01-jobs-portal` | Jobs | every job folder, one card each, plus a way to start a new one |
| `02-new-job-roads` | New job, choice | two ways in: type it, or drop the engagement letter (second not built) |
| `03/04-new-job-form` | New job, form | intake, split into "needed to start" and "can wait", with the folder name deriving itself. Empty and filled, so you can see the disabled and enabled primary button |
| `05-job-home` | Job | the densest screen. What has arrived from the folders on the left, the report's sections in print order on the right |
| `06-photos-grid` | Photos | photo grid with an editable caption under each |
| `07-photos-build-done` | Photos, after build | the success banner state |
| `08-caption-sheet` | Caption chooser | an overlay showing how the printed page will read, with a segmented control between two caption styles |
| `09-settings-key-off` | Settings | one card per thing you can set, with an on/off lamp |
| `10-section-picker` | Sections | a checklist of the report's sections for this kind of appraisal |

All data in these captures is synthetic. No real client, address, or valuation appears anywhere.

## Known problems, so you do not reproduce them

**Confirmed defects:**

- Photo captions render in **monospace at 13.33px** instead of the app's Helvetica at 14px. The CSS declares `font: 14px/1.45 inherit`, and `inherit` is not valid inside the `font` shorthand, so the whole declaration is dropped and the browser falls back to its default. Visible in `06`, `07`.
- Captions are **clipped**. The field is `overflow: hidden` with a fixed min-height, and pre-filled captions never trigger the auto-grow, so Mark cannot read the end of his own caption. Visible in `06`, `07`.

**Structural problems:**

- **15 distinct font sizes**, including 10.5, 11.5, 12.5, 13.5 and 14.5. There is no type scale.
- **22 distinct spacing values**, nearly every integer from 2 to 30. There is no spacing grid.
- **7 border radii**: 2, 3, 4, 5, 6, 8, 999.
- **13 hardcoded hex values** outside the token block.
- The masthead mark is an inline SVG that hardcodes the wrong red three times and approximates the logo with three plain bars, missing the angled cut.

**Things that look intentional and probably are:**

- The job screen is a deliberately uneven two-column split (1.45fr / 1fr) because the left column carries long "still needs" lists that wrap badly when squeezed.
- The page is 1200px rather than 960 for the same reason.
- The caption chooser is an overlay rather than a settings toggle, on purpose: it is a step in the action, not a parked option.

## What would help most

Rather than a restyle, the useful output is a **system**: a type scale, a spacing grid, a small set of surfaces and states, and a component set that covers the surface above. The current app has roughly 25 recurring pieces (cards, rows, chips, panels, fields on light and on dark, lamps, banners, an overlay, a segmented control, a checklist, a photo grid, a printed-page preview). Whether those are the right 25 is exactly the question worth arguing about.

States matter more than looks here. The missing states are what forced the ad-hoc values in the first place: disabled, loading, empty, error, "not built yet", and the has/needs distinction on the job screen.

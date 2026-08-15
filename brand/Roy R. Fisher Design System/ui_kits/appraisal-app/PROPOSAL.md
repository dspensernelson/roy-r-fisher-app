# The proposal — one way the app could work

**Nothing in this file is binding.** It records the product decisions embodied in
`index.html` and the reasoning behind each, so the builder can overrule any of
them without unpicking the design system to do it. The design system's actual
asks are the Tier 1 list in the root `readme.md`; everything below is argument.

Open `index.html` — plain HTML, CSS and vanilla JS, no framework and no CDN, so
it opens offline anywhere. All data is synthetic: no real client, address or
valuation appears.

## The decisions, and the reasoning

**The job screen is a worklist, not a comparison.** The old screen set what had
arrived beside what the report needed. That is a comparison, and comparisons
make the reader do the arithmetic. The proposal orders it instead: *what can you
do right now, without waiting on anyone*.
→ *Overrule this if* Mark's real bottleneck is tracking the report's shape rather
than deciding what to touch next.

**Rows are mixed: actions on top, the report's sections alongside.** One row per
missing thing rather than one per folder, because a folder is where a file
lives, not a task.
→ *Overrule this if* the folder view is how he actually thinks about a job.

**Nothing claims who is holding something up.** The app reads folders; it does
not know the rent roll is with the owner. An earlier draft had a "waiting on
someone else" group with chips saying *With the owner* — invented state the app
cannot support. Things he cannot do yet appear as *"waiting on the rent roll"*
on the **section rows only**.
→ *Overrule this if* the builder gives Mark a way to mark a request as sent; then
the group becomes honest and should come back.

**Every gap is a task, and each task names its consequences.** "Add the assessor
PRC — Site Analysis and Description of Improvements are both waiting on it. Goes
in Subject Information." The *why* is what makes it a plan rather than a list of
gaps, and it requires the app to know which sections depend on which inputs.
→ *Overrule this if* that dependency map is more than the section engine can
carry; the rows still work without the second line, just less usefully.

**"Already here" stays visible and open.** Three rows of things he already knows,
kept because reassurance is part of this app's copy — it is the same instinct as
"your originals stay untouched".
→ *Overrule this if* the list grows long enough to bury the tasks.

**Job cards carry their own next action and progress**, so the Jobs grid answers
*which job needs me* without opening anything.
→ *Overrule this if* computing "next action" for every job on every load is too
expensive.

**Only one red rule per screen.** The next task gets it; the rest are hairline.
Six red rules is wallpaper, and it contradicts what the rule is supposed to mean.

**The folder set follows the engagement type** — nine folders for a tax appeal,
eleven for a full appraisal — and intake says so before it makes anything.
→ *This one is a guess at the numbers.* The real matrix lives in `shop/data/`.

**No loading state for the folder scan.** The scan is under a second, so screens
navigate and the rows are simply there. The sweep is for captions and document
building only, where the wait is real.
→ *Overrule this if* the scan gets slower; then rows should stream in under the
band heading rather than the screen blocking.

## Known open questions

- **"Which way it faces" needs a way for Mark to approve the direction.** If the
  app infers it, he must be able to correct it — that is a per-photo confirm, a
  different overlay from the style chooser. If he supplies it, it is a field, not
  a caption style. The two readings produce different screens.
- **Facing may only apply to roads and right-of-way work.** If so the option
  should not appear for a retail or office job at all, and the segmented control
  would have one option and stop being a control. This belongs in the engagement
  matrix alongside the folder set and section list.
- **Whether `FolderCard` survives.** The proposal moved to task rows, but a
  per-folder view of the scan is still the honest way to show what is on disk.
  Both components exist; only one is used.

## The screens

| Screen | What it does |
| --- | --- |
| Jobs | every job folder as a card carrying its next action and progress, plus the new-job slot |
| New job (roads) | two ways in; the unbuilt one is shown and tagged, not hidden |
| New job (form) | intake split into "needed to start" and "can wait"; the folder name derives itself until edited |
| Job | the worklist, with the report's sections alongside |
| Sections | the checklist for this engagement shape |
| Photos | the grid, drag to reorder, captions that grow, the build banner |
| Caption chooser | the overlay: a printed-page facsimile with the style control at the head of the caption column |
| Settings | one card per thing you can set, with a word for its state |

## What to try

- Click a job card, then the red-ruled **Subject Photographs** row — the only section that builds today.
- On Photos, press **Suggest captions**: the question is asked inside the action, over a facsimile of the printed page. Switch the control and the captions change.
- Press **Use this style** — captions already typed are left alone; empty ones fill in.
- Press **Build photo pages** for the working sweep and the done banner.
- Drag one photo tile onto another to reorder.
- Press **+ New job**, then **Read the engagement letter** to see the unbuilt route and its caution. Fill in address, city and both dropdowns to watch the folder name derive itself and the primary button enable.
- In Settings, type anything and press **Check and save** to watch the lamp go Off → Checking → On.

## Files

| File | What it is |
| --- | --- |
| `index.html` | the whole click-through — seven screens, the overlay, ~120 lines of vanilla JS |
| `*.jsx` | the same screens composed from the design system's React components, for a project with a build step; not what `index.html` loads |
| `data.js` | the synthetic job, folder, section, task and photo data used by the JSX version |

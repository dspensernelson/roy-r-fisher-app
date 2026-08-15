# Roy R. Fisher

A Windows desktop app that helps Mark produce commercial appraisal reports.
Mark runs Roy R. Fisher in Davenport, Iowa. He has written these reports in
Word for decades and is not a software user by inclination. Spenser owns the
product. The app runs on one machine, offline, for one person.

## What is at the root

| | |
|---|---|
| `app/` | The product. Python server, React screens, its own engine and templates. Stands on its own; nothing in it reads anything outside itself |
| `brand/` | The design system source: components, tokens, and the real logo and photography files |
| `Start Roy R. Fisher.command` | Double-click to run it on a Mac |

## What is deliberately not here

Mark's delivered appraisals are his clients' confidential work, so they are
not in this repository and will not be. Neither is his own folder template,
which lives inside one of them. They stay on the development machine.

Several tests read that material to check the built Word file against a real
delivered report. On a clone without it they skip, and say which private file
they wanted. Everything else runs.

The previous version of this project, a set of AI skills that drafted reports
by following written instructions, is also not here. It is kept as a local
archive.

## What the app does today

Mark can make a job from a form, and it creates his own eight folders on disk,
named the way he names them. He can pick which sections the report needs, and
the app proposes a list from the kind of appraisal. He can see what has
arrived in his folders next to what the report still needs. He can build the
subject photo pages, which produces a real Word file. He can set up his own
API key on a settings screen.

Photo pages are the only section that produces a document. Everything else is
listed so the report's real shape is visible, and says plainly that it is not
ready yet.

109 tests pass.

## What we know is missing

- **There is no Windows launcher.** The only way to start it is a Mac shell
  script. A `.bat` twin is a chore, not a hard problem, and nothing else is
  Mac-specific in the app's path.
- **The design system has not been adopted.** The screens still run on the old
  stylesheet, whose brand red is wrong.
- **No section other than photos builds.** The next cheapest family is the
  image pages: aerial photo, neighborhood map, plat map, building sketch,
  comparable sales map. Same machinery as photos, which is proven.
- **Reading an engagement letter is offered on screen but not built.**
- **Turning the finished Word files into a delivered PDF is not built**, and
  the old tool for rendering numeric grids drives Excel through Mac-only
  automation.

## Running it from a fresh clone

The web interface is built from source and the built files are not committed,
so a fresh clone needs one step before the app will serve anything:

    cd app/web && npm ci && npm run build

Then start it with `Start Roy R. Fisher.command` on a Mac, or
`python3 app/run_app.py`.

Mark will not have Node on his PC. Whatever we eventually hand him has to
arrive with the interface already built, so that build is a packaging job for
us and never a step for him.

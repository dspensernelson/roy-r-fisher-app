# Roy R. Fisher

A Windows desktop app for producing commercial appraisal reports. It is built
for one commercial appraiser, who has written these reports in Word for
decades. Spenser owns the product. The app runs on one machine, offline,
for one person.

## How this gets built

`HOW-WE-WORK.md` is the standard this project is held to. It is the rules the
build has to clear and the reasoning behind each one. If you want to know how
the app got made rather than what it does, read that first.

## What is at the root

| | |
|---|---|
| `app/` | The product. Python server, React screens, its own engine and templates. The code reads no project files outside app/. At run time it also uses the settings and key files in the home folder and the jobs folder the appraiser points it at. One dev tool reaches wider: demo reset finds the repo root. One styling test reads the design system and skips without it |
| `Start Roy R. Fisher.command` | Double-click to run it on a Mac |

## What is deliberately not here

The delivered appraisals are his clients' confidential work, so they are
not in this repository and will not be. Neither is his own folder template,
which lives inside one of them. They stay on the development machine.

Several tests read that material to check the built Word file against a real
delivered report. On a clone without it they skip, and say which private file
they wanted. Everything else runs.

The design system and the firm's brand assets, its logo, letterhead and
photography, are also not here. They are the firm's property rather than this
project's, so they stay on the development machine. One styling test reads
them and skips on a clone without them.

The previous version of this project, a set of AI skills that drafted reports
by following written instructions, is also not here. It is kept as a local
archive.

## What the app does today

The appraiser can make a job from a form, and it creates his own eight folders on disk,
named the way he names them. He can pick which sections the report needs, and
the app proposes a list from the kind of appraisal. He can see what has
arrived in his folders next to what the report still needs. He can build the
subject photo pages, which produces a real Word file. He can set up his own
API key on a settings screen.

Photo pages are the only section that produces a document. Everything else is
listed so the report's real shape is visible, and says plainly that it is not
ready yet.

335 tests; the ones that need that private material skip on machines without it.

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

The target PC will not have Node. Whatever we eventually hand him has to
arrive with the interface already built, so that build is a packaging job for
us and never a step for him.

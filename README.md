# Roy R. Fisher

**This is the active Roy R. Fisher application repository.**

Application code, builds, packaging, tests, and current documentation live
here. This is the only copy. If you are running the app or changing it, you
are in the right folder.

Source reports and evidence live next door in `RRF`. That folder holds
Mark's finished reports and reference material, and no application code.

Do not create a second copy of the app inside `RRF`. One existed until
2026-08-21, went stale, and made it unclear which folder to open.

| Want to | Go to |
|---|---|
| Run or change the app | `RRF-App` (this folder) |
| Find reports or evidence | `RRF` |

---

A Windows desktop app that helps Mark produce commercial appraisal reports.
Mark runs Roy R. Fisher in Davenport, Iowa. He has written these reports in
Word for decades and is not a software user by inclination. Spenser owns the
product. The app runs on one machine, offline, for one person.

## What is at the root

| | |
|---|---|
| `app/` | The product. Python server, React screens, its own engine and templates. The code reads no project files outside app/. At run time it also uses the settings and key files in the home folder and the jobs folder Mark points it at. Two dev tools reach wider: demo reset finds the repo root, and one styling test reads brand/ |
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

335 tests; the ones that need Mark's private material skip on machines without it.

## What we know is missing

- **Nothing has run on Windows yet.** There is now a Windows launcher, a
  packaging script, and a package that builds and self-verifies on the Mac
  (`tools/package_windows.py`). Whether the embedded interpreter starts, the
  compiled wheels import, and Explorer's unzip leaves it whole are all still
  unproven, and are the next thing to be tested.
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
`python3 app/run_app.py`. Both take the same path now: the launcher picks a
free port rather than assuming 8000, waits for the app to really answer before
opening the browser, and refuses to start a second copy while another version
is running.

Mark will not have Node on his PC. Whatever we eventually hand him has to
arrive with the interface already built, so that build is a packaging job for
us and never a step for him.

## Building the Windows package

    python3 tools/package_windows.py

Produces `build/windows/Roy R. Fisher vX.Y.Z/`: the app, the built interface,
an embedded CPython 3.14, the whole runtime dependency closure resolved for
`win_amd64`, and a MANIFEST the launcher checks before it imports anything.
The build output is not committed. Add `--offline` to lay out and verify the
package without downloading the interpreter and the wheels.

# Bugs

The app does something wrong and somebody is affected today. Every entry says
what happens, who it hits, and how bad it is. Items leave this file when they
are fixed, and whatever they taught goes to `docs/ROADMAP.md`.

If nothing is broken, it is not a bug. It goes in `docs/FUTURES.md`.

Found on 2026-09-03, in the first real day of use, by Colleen McDevitt Brown in
Mark's office, on the COAL VALLEY_2377 US Highway 6 (Kennel) job.

---

## The audit of 2026-09-16

Every entry below was read against the code on `working`, not against the
commit that claimed to close it. **Thirteen of the sixteen were already fixed
and nobody had checked.** Three are live: B4, B10 and B12.

Commit messages were not trusted, and the reason is in B12: a commit titled
"docs: the update box must fill the width" changed no CSS whatsoever.

Two marks in this file were true and had gone stale. B7 and B9 both said
"Fixed on branch, not yet shipped". Both are on `working` and both shipped to
the office in 0.7.6 on 2026-09-16.

Each entry now opens with a verdict line. A verdict without a `file:line`
beside it is not a verdict.

---

## One cause under four of these

**FIXED, 2026-09-16.** Checked against the code at `app/server/photos.py:653-683`.

**`Add a photo` writes the file to the top of the `Photos` folder. The report
reads from the subfolder Mark's office chose.** So the app puts the photograph
somewhere the report cannot see, and every reconciliation afterwards treats it
as an outsider that does not belong.

Spenser worked this out on 2026-09-03 from the behaviour alone. Confirmed in
`app/server/photos.py` `store_upload`, which always writes to
`jobs.photos_dir(job)`, against `_report_set`, which keeps only entries whose
`folder` matches the chosen one.

**B1, B2, B3 and B5 are all that one fault wearing different clothes.**

---

## B15. Every new version fails the first time it runs

**FIXED, 2026-09-16.** Checked against the code at `app/run_app.py:238,256-258`, and 0.7.6 is at the office.

**What happens.** A version that has never run before dies instantly at
startup. No window, no message, nothing. Run it a second time and it works, and
then it works for ever. So it looks random and looks like it fixed itself.

**Proven on Spenser's Windows machine, 2026-09-15.** 0.7.5 crashed three times
out of three from a cold install. Comparing the two installed copies file by
file showed the only differences were `.pyc` cache files, the version, and the
browser files. 0.7.4's cache was warm from dozens of runs. 0.7.5's had never
been written. Warming it by crashing three times was enough: the fourth run
started and it has worked ever since.

**Why, from the traceback.** `app/run_app.py` starts three background jobs and
then, on the very next line, imports uvicorn. On a cold start those jobs must
compile hundreds of files, which takes long enough that the uvicorn import
reaches `dataclasses` while a background job still has `typing` half built. It
reads the half-built module and dies:

    AttributeError: partially initialized module 'typing' has no attribute
    'ClassVar' (most likely due to a circular import)

Warm cache, the background jobs finish in a blink and nothing collides.

**Who it hits.** Everyone, on every update and every fresh install, because
both are cold starts by definition. This is one fault wearing four faces, and
all four were reported as separate problems during the week of 2026-09-08:

- Colleen's Desktop icon doing nothing, then an older version updating and
  working.
- The loading page saying the app had probably opened in another tab when it
  had not.
- 0.7.5 installing through the update button and never answering.
- "Nothing happens for a few seconds after you click the icon", B14 below.

**How bad.** The worst on this list. It is the first thing that happens to
anybody on any new version, and it destroys the update button, which is the
only way the office gets anything.

**The fix.** Start those three background jobs after the web server is loaded,
not before. `app/run_app.py` lines 214 to 218.

**Nobody saw the error because the launcher throws it away.** It speaks for two
named failures and sends everything else nowhere, since the shortcut runs
`pythonw.exe`, which has no console. That gap hid this for a week and is its
own item.

**Built in 0.7.5.1, not yet proven.** The three background jobs now start after
uvicorn is imported, and anything unexpected now reaches both the log and a
message box that says to start it again and which file to send. Two tests hold
the order, one on the source and one while the launcher runs. Neither can prove
a cold Windows start, because every machine the tests run on is warm. This
entry stays open until 0.7.5.1 is installed cold on Spenser's Windows machine
and opens first time.

---

## B1. Generating captions deletes photographs you added

**FIXED, 2026-09-16.** Checked against the code at `app/server/photos.py:549-591`.

**What happens.** Add a photograph with `Add a photo`. Run captions. The
photograph is gone. Building then fails saying it is not in the project.

**Who it hits.** Colleen. It stopped a real report on 2026-09-03.

**How bad.** Worst on this list. It destroys work after money has been spent on
captions, and the error it produces points at the wrong thing.

**Note.** "That photo is not in this job" is the symptom. Captions removing the
photograph is the cause. Do not fix the message.

## B2. Taking out a photograph you added leaves a second copy behind

**FIXED, 2026-09-16.** Checked against the code at `app/server/photos.py:1085-1123`.

**What happens.** Take out a photograph added with the button. A duplicate
appears in the folder it came from.

**Who it hits.** Colleen, and then Mark, because the duplicate is left sitting
in a client's folder.

**How bad.** High. The app is writing into Mark's own folders, which is the one
thing `HOW-WE-WORK.md` says it must never do.

## B3. Taking out one photograph takes the others with it

**FIXED, 2026-09-16.** Checked against the code at `app/server/photos.py:1108-1119`.

**What happens.** Two photographs added. One taken out. Both gone.

**Who it hits.** Colleen. Loses work with no warning.

**How bad.** High.

## B4. A photograph you removed stays in the list and blocks everything

**STILL LIVE, 2026-09-16.** Checked against the code at `app/server/main.py:1264` and `app/server/photos.py:479`.
The half he called the dead end is gone. What remains is worse than the entry describes: the build still refuses and names a photograph, while `load_manifest` drops any entry whose file is missing before the screen sees it, so the photograph it tells her to take out has no tile to take out. No test covers that message or that path.

**What happens.** The build refuses:

    Build failed: Mallard Pointe road sign 2 (3).png is named in
    photo-manifest.json but is not in the Photos folder.

There is no way past it. `Clear captions` is blocked by the same check, so she
cannot start over either. From her log:

    11:01:22  POST .../build            status=500
    11:03:48  POST .../build            status=400
    11:04:15  POST .../captions/clear   status=400

**Who it hits.** Colleen. A dead end with no door.

**How bad.** High. Being unable to undo is worse than the original fault.

## B5. Photographs added with the button do not appear

**FIXED, 2026-09-16.** Checked against the code at `app/server/photos.py:671-683`.

**What happens.** They land at the top of `Photos`. The report points at a
subfolder. The screen filters them straight back out.

**Who it hits.** Colleen. It reads as the app throwing her work away.

**How bad.** High.

## B6. The photo screen sits on `Loading...` for ever and hides the reason

**FIXED, 2026-09-16.** Checked against the code at `app/web/src/screens/PhotosScreen.jsx:438-446`.

**What happens.** When the job's photo list cannot be read, the screen shows
`Loading...` and never changes. On 2026-09-03 the only way out was deleting
`photo-manifest.json` by hand, which risked every caption in it.

**Why, proven in the code.** `app/web/src/screens/PhotosScreen.jsx:216`:

    if (!manifest) return <p className="sub">Loading...</p>;

The lines that display an error are at 240, 277 and 607, **all below it**. The
error is caught, stored in state, and then never reached. The screen is holding
the explanation and cannot show it.

Her log shows the read failing twice before she gave up:

    10:48:57  GET .../manifest  status=400
    10:50:33  GET .../manifest  status=400

**Who it hits.** Colleen, and anyone whose photo list is ever unreadable.

**How bad.** High. A dead screen with the answer in its pocket.

## B7. `Show the log` opens a window behind everything and says nothing

**FIXED, 2026-09-16.** Checked against the code at `app/server/main.py:631-648` and `app/web/src/screens/Settings.jsx:176-207`, shipped in 0.7.6.

**What happens.** The folder opens behind the browser. Nothing on screen
changes, so the button looks broken and gets clicked again. Each click starts
another File Explorer. From the log of 2026-09-02, thirteen clicks in
thirty-seven seconds, each one slower than the last:

    22:00:47  POST /api/log/show  ms=243
    22:00:53  POST /api/log/show  ms=3726

**Who it hits.** Spenser, and Colleen the moment she needs to send a log.

**How bad.** Medium. It is also the exact fault this button existed to prevent:
the app does something and says nothing.

**Fixed on branch `send-the-log-to-spenser`, 2026-09-14. Not yet shipped.** The
folder window is gone entirely rather than improved. `Show what will be sent`
puts the text on the screen with a `Copy` button, and `Send the log to Spenser`
sends it. The button that goes says `Sending...` and cannot be pressed twice,
which is the half of this that made thirteen clicks possible.

## B8. The app opens behind the black window

**FIXED, 2026-09-16.** Checked against the code at `Start Roy R. Fisher.bat:17` and `app/install_windows.py:373-387`.

**What happens.** The console window is in front when the app starts. Spenser's
words on 2026-09-03: *"I just want the app to open like an app."*

**Who it hits.** Everybody, every single time they start it. It is the first
thing anyone sees.

**How bad.** Medium in effect, high in what it says about the product.

---

# Found on 2026-09-03, testing the update on Spenser's virtual machine

**The update button itself worked, for the first time ever.** It found 0.6.4,
downloaded it, checked it, installed it and closed the app. Everything below is
about how that felt, not whether it worked.

## B9. `Check now` points at a button that is not on the screen

**FIXED, 2026-09-16.** Checked against the code at `app/web/src/screens/Settings.jsx:94` and `app/web/src/App.jsx:110-112,354`, shipped in 0.7.6.

**What happens.** Settings says "Version 0.6.4 is available. Use the Update
available button at the top of the screen." There is no such button.

**Why.** The masthead asks the server about updates once, when the page loads,
and nothing tells it to ask again. `Check now` updates what the server
remembers; the notice at the top is still holding the answer from before the
newer version existed.

**The way past it today.** Press `Check now`, then reload the page. The button
appears.

**How bad.** High. The app tells you to do something you cannot do.

**Fixed on branch `the-update-button-appears`, 2026-09-03. Not yet shipped:
0.6.3 and 0.6.4 both have it.**

## B10. The screen never closes after an update

**STILL LIVE, 2026-09-16.** Checked against the code at `app/web/src/screens/UpdateStep.jsx:96-111`.
Half fixed. The panel is a full-screen cover now rather than a layer over a live job list. The tab still never closes and nothing confirms the new version started.

**What happens.** The app says "Closing now", the server stops, and the tab
sits there for ever showing that sentence on top of a job list that looks
usable and is not. Nothing tells you the new version has started.

**Why.** The panel is a notice laid over a live screen, so when the server dies
the last render just stays there. There is nothing to replace it, because there
is no longer an app to replace it.

**How bad.** High. The last thing the app does before handing over is look
broken.

## B11. The black window

**FIXED, 2026-09-16.** Checked against the code at `app/server/tell.py:45-53` and `app/run_app.py:314-336`.

**What happens.** A console window opens in front of the app, empty, and stays
there the whole time it runs.

**Spenser, 2026-09-03:** *"I just want the app to open like an app."*

**What it needs.** `pythonw.exe` ships inside the package and runs with no
console at all. The catch is that it also has nowhere to print, so a startup
failure would be silent, which is worse. The failure has to become a real
dialog box and a line in the log.

**How bad.** Medium in effect. High in what it says. It is the first thing
anybody sees, every time.

## B12. The update box sits narrow on the left instead of spanning the screen

**STILL LIVE, 2026-09-16.** Checked against the code at `app/web/src/brand.css:227` and `:1052`.
**Worse than this entry says.** `.confirm` is still capped at 720px and `.update-step` now adds a 560px cap, so the box is narrower than when the bug was written. The commit `fab1192`, "docs: the update box must fill the width", changed no CSS at all.

**What happens.** The "Update to version 0.6.5?" box stops at 720px and leaves
open space to its right instead of filling the width Settings gives it.

**Why, proven in the code.** `app/web/src/brand.css:137-138`, the `.confirm`
class: `max-width: 720px`. `UpdateStep.jsx` uses that class for this box.

**Check across all boxes of this kind before fixing.** `.confirm` is not this
screen's own class. It is shared by six other boxes: one in `App.jsx:157`
and three in `PhotosScreen.jsx` (284, 484, 807), each rendered at different
points in the photo workflow. Widening `.confirm` itself changes all of them
at once. Whoever fixes this has to look at each one and decide whether 720px
was deliberate there too, not just widen the class and assume the rest follow.

**Who it hits.** Spenser, seen 2026-09-03. Anybody who opens Settings once an
update is available.

**How bad.** Medium. Nothing is broken, it just looks unfinished.

## B13. Typing a caption, then hitting `Mark reviewed` without clicking away first, throws the caption away

**FIXED, 2026-09-16.** Checked against the code at `app/web/src/screens/PhotosScreen.jsx:301,410`.

**What happens.** Type a caption. Do not click anywhere else. Click `Mark
reviewed` while the cursor is still in the box. The caption reverts to
whatever it was before you started typing.

**Why, proven in the code.** `PhotosScreen.jsx:687-689`. The textarea's
`onChange` only updates the screen's own copy of the manifest, through
`setCaption` (line 207), which never talks to the server. The caption is only
written to disk `onBlur`. `Mark reviewed` (line 698, `onReview` at line 159)
calls the server directly and replaces the screen's manifest with whatever it
sends back. If the box never lost focus, the server never received the new
caption, so it hands back the old one, and that old one overwrites what is
still sitting, unsent, on screen.

**Who it hits.** Anybody who writes a caption and reaches straight for `Mark
reviewed` without clicking elsewhere first. Found by Spenser, 2026-09-07.

**How bad.** High. It looks like the click did nothing, but it silently
throws away what was just typed, with no warning and nothing to undo it with.

## B14. Nothing happens for a few seconds after you click the icon

**FIXED, 2026-09-16.** Checked against the code at `app/run_app.py:134` and `app/server/splash.py:198-213`.

**What happens.** Double-click `Roy R. Fisher`. Nothing. No window, no
hourglass, no sign the click landed. Some seconds later the browser opens.

Spenser, 2026-09-03: *"the app opened once but I can't get it to open again"*,
and then, a moment later: *"wait, it worked."*

**Why.** Taking the black window away took the only proof the click had done
anything. The app checks the package, picks a port, starts the server, waits
for it to really answer, and only then opens the browser. All of that used to
happen with a window in front of you saying "Starting Roy R. Fisher". Now it
happens in silence.

**Not the same as B11 and not a reason to bring the window back.** The window
was the wrong answer to a real need. Clicking again is harmless, because since
0.7.1 the second copy stops the first and takes over, but a person who sees
nothing has no way to know that.

**How bad.** Medium. It is the first thing that happens every time anybody
uses the app, and it currently looks like a click that failed.


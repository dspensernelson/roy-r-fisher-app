# Bugs

The app does something wrong and somebody is affected today. Every entry says
what happens, who it hits, and how bad it is. Items leave this file when they
are fixed, and whatever they taught goes to `docs/ROADMAP.md`.

If nothing is broken, it is not a bug. It goes in `docs/FUTURES.md`.

Found on 2026-09-03, in the first real day of use, by Colleen McDevitt Brown in
Mark's office, on the COAL VALLEY_2377 US Highway 6 (Kennel) job.

## One cause under four of these

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

## B1. Generating captions deletes photographs you added

**What happens.** Add a photograph with `Add a photo`. Run captions. The
photograph is gone. Building then fails saying it is not in the project.

**Who it hits.** Colleen. It stopped a real report on 2026-09-03.

**How bad.** Worst on this list. It destroys work after money has been spent on
captions, and the error it produces points at the wrong thing.

**Note.** "That photo is not in this job" is the symptom. Captions removing the
photograph is the cause. Do not fix the message.

## B2. Taking out a photograph you added leaves a second copy behind

**What happens.** Take out a photograph added with the button. A duplicate
appears in the folder it came from.

**Who it hits.** Colleen, and then Mark, because the duplicate is left sitting
in a client's folder.

**How bad.** High. The app is writing into Mark's own folders, which is the one
thing `HOW-WE-WORK.md` says it must never do.

## B3. Taking out one photograph takes the others with it

**What happens.** Two photographs added. One taken out. Both gone.

**Who it hits.** Colleen. Loses work with no warning.

**How bad.** High.

## B4. A photograph you removed stays in the list and blocks everything

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

**What happens.** They land at the top of `Photos`. The report points at a
subfolder. The screen filters them straight back out.

**Who it hits.** Colleen. It reads as the app throwing her work away.

**How bad.** High.

## B6. The photo screen sits on `Loading...` for ever and hides the reason

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

**What happens.** The folder opens behind the browser. Nothing on screen
changes, so the button looks broken and gets clicked again. Each click starts
another File Explorer. From the log of 2026-09-02, thirteen clicks in
thirty-seven seconds, each one slower than the last:

    22:00:47  POST /api/log/show  ms=243
    22:00:53  POST /api/log/show  ms=3726

**Who it hits.** Spenser, and Colleen the moment she needs to send a log.

**How bad.** Medium. It is also the exact fault this button existed to prevent:
the app does something and says nothing.

## B8. The app opens behind the black window

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

**What happens.** The app says "Closing now", the server stops, and the tab
sits there for ever showing that sentence on top of a job list that looks
usable and is not. Nothing tells you the new version has started.

**Why.** The panel is a notice laid over a live screen, so when the server dies
the last render just stays there. There is nothing to replace it, because there
is no longer an app to replace it.

**How bad.** High. The last thing the app does before handing over is look
broken.

## B11. The black window

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


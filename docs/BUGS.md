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

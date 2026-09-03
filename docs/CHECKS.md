# Checks

Things to try by hand, on a real machine, in plain words. Three lines each.
Short enough to hand to somebody else and have them actually do it.

These are not the automatic tests. `python3 -m pytest` proves the parts. These
prove the app, on Windows, on a real job, which is where every fault so far has
actually turned up.

**Run these on the virtual machine before anything reaches Mark's office.**

Say the number when one fails. "Check 2 failed" is enough to start from.

---

## The photographs you add

> ### Check 1. A photograph you add stays added
> Click **`Add a photo`** in the app. Pick a photograph from anywhere on the
> computer.
> **Should:** it appears on the screen, and it is still there after you
> generate captions, after you take a different photograph out, and after you
> build.
> **Wrong if:** it disappears at any of those, or takes another photograph with
> it.

> ### Check 2. Taking one out leaves nothing behind
> Add a photograph with the button. Take it out. Open the folder it came from
> in File Explorer.
> **Should:** exactly what was in that folder before, and nothing else.
> **Wrong if:** there are now two copies of it.

> ### Check 3. Taking one out takes only that one
> Add two photographs with the button. Take out one of them.
> **Should:** the other one is still there.
> **Wrong if:** both go.

> ### Check 4. Adding then captioning keeps everything
> Add a photograph with the button. Generate captions for the job.
> **Should:** every photograph that was there before is still there, and so is
> the new one.
> **Wrong if:** anything is missing afterwards.

## Getting out of trouble

> ### Check 5. Nothing stops you with no way forward
> Build the report.
> **Should:** it builds, or it refuses and offers you something you can do
> about it.
> **Wrong if:** it refuses and there is nothing on the screen that gets you
> past it.

> ### Check 6. Clear captions always works
> On a job with captions, click **`Clear captions`**.
> **Should:** the captions go, every time, whatever else is wrong with the job.
> **Wrong if:** it refuses.

> ### Check 7. The screen never sits on `Loading...`
> Open a job's photographs.
> **Should:** either the photographs appear, or a sentence tells you what is
> wrong.
> **Wrong if:** it says `Loading...` and stays there.

## Starting the app

> ### Check 8. The app comes to the front
> Start the app the way Mark starts it.
> **Should:** the app is the thing you are looking at.
> **Wrong if:** a black window is in front of it, or instead of it.

> ### Check 9. `Show the log` shows you the log
> Open Settings, click **`Show the log`**.
> **Should:** you can read the log and copy it, without hunting for a file.
> **Wrong if:** nothing appears to happen.

## Updating

> ### Check 10. The update button finds a newer version
> With a newer version published, open Settings and click **`Check now`**.
> **Should:** it names the newer version.
> **Wrong if:** it says you are on the newest version when you are not.

> ### Check 11. The update button installs it
> Take the update it offers, and let it run to the end.
> **Should:** the app restarts on the new version, and the job folders are
> untouched.
> **Wrong if:** anything about the jobs changed, or the app does not come back.

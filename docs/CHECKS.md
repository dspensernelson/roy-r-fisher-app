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
> Open Settings and find **`Show the log`**. It is blue writing with no box
> round it, not a button. Click it.
> **Should:** you can read the log and copy it, without hunting for a file.
> **Wrong if:** nothing appears to happen, or it is a coloured button.

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

> ### Check 12. The update waits to see the new version really start
> Take the update, and watch the window it opens all the way to the last line.
> **Should:** it says `Waiting for it to answer...` and then names the version
> as open. If the new version never starts, it says so instead and puts
> `Go back to the last version` on the Desktop.
> **Wrong if:** it says the update worked while the app is not running.

## Excel and Word

> ### Check 13. The app can drive Excel and Word on this computer
> Open a Command Prompt in the app's folder and run:
> `program\python\python.exe program\app\engine\office_check.py`
> **Should:** it prints five numbered steps and ends with "Everything worked".
> **Wrong if:** it stops at a step, or nothing happens for minutes with no
> message. If nothing happens, look at Excel and Word: one of them is showing
> a box waiting for you.

> ### Check 14. A real grid comes out looking like his report
> Run the same line again with one of Mark's workbooks, a sheet name and a
> range after it, then open the PDF it made.
> **Should:** the grid is in the PDF, with its heading, its shading, its
> borders and its money, and nothing is cut off at the edge.
> **Wrong if:** any column is clipped, colours are wrong, or the grid is
> missing.

## Starting the app, new in 0.7.0

Version 0.7.0 shows a loading page while the app gets going. The page is a file
on the computer and the app is a program on the same computer, and the page has
to reach the program for any of this to work. Nobody has yet watched that happen
on Windows. Check 15 is the one that finds out.

> ### Check 15. The loading page turns into the app. **Read this one twice.**
> Start the app the way Mark starts it. A page opens saying
> `Starting version 0.7.0`. Watch it and touch nothing.
> **Should:** within about ten seconds that same page becomes the app, in the
> same tab. No second tab and no second window.
> **Wrong if:** it is still saying `Starting` after half a minute. If it is,
> **do not sit and wait.** Double-click the icon again while the first page is
> still saying `Starting`. If the app opens now, then the app had been running
> the whole time and the loading page could not reach it. **That is the worst
> fault in this version. Stop there and tell Spenser.** Left alone, the page
> waits two and a half minutes and then says the app did not start, which is
> not true, and nothing on screen would ever tell you otherwise.

> ### Check 16. Starting it twice does not give you two of it
> With the app already open and working, double-click the icon again.
> **Should:** you are put back in front of the app you already had. No loading
> page this time, because there is nothing to wait for.
> **Wrong if:** a loading page appears, or a second copy starts, or you are told
> another version is running.

> ### Check 17. A damaged copy still stops you
> Copy the whole version folder to the Desktop. In the copy only, open
> `program\app\web\dist\index.html` in Notepad, type a word into it, save, and
> start that copy. Throw the copy away afterwards.
> **Should:** a box says the program is damaged, and the app does not open.
> **Wrong if:** it opens anyway, or the loading page sits there for two and a
> half minutes and no box ever appears.

## The captions you type

> ### Check 18. A caption you have just typed is not thrown away
> Open a job's photographs. Type a caption into one. Without clicking anywhere
> else first, click the tick underneath that same photograph.
> **Should:** the tick goes on and your words are still in the box. Leave the
> job, come back, and they are still there.
> **Wrong if:** the box goes back to what it said before, or goes empty.

> ### Check 19. Typing a caption does not reach across the network
> On a job that lives on the office network disk, type a long caption quickly.
> **Should:** the letters keep up with your fingers, and nothing else on the
> screen moves while you type. The number on `Generate captions` sits still.
> **Wrong if:** the letters lag behind, or that number flickers or changes as
> you type.

> ### Check 20. The price you agree to is the price of what is there now
> Open a job's photographs, add two more photographs, then click
> `Generate captions` and read the figure on the step that asks you to agree.
> **Should:** the figure counts the ones you just added, because it is worked
> out again at that moment.
> **Wrong if:** it shows a price from before you added them, or shows no price.

## Colour

Colour now answers one question only: can he take it back? It says nothing about
how important a control is. The full rule is in `docs/ROADMAP.md`, 2026-09-08.

> ### Check 21. One solid red button on a screen, at most
> Walk through Jobs, a job, its Photographs, its Sections, and Settings. Count
> the solid red buttons on each screen.
> **Should:** never more than one, and it is the thing you came to that screen
> to do. In the whole app there are three: `Build photo pages`, `Make the job`,
> `Update now`.
> **Wrong if:** two solid red buttons share a screen, or a solid red button only
> cancels, closes, or goes back. Red lines are not buttons: the band across the
> top of the screen and the line along the top of a card are meant to be red.

> ### Check 22. The way out is never the loudest thing
> On every screen that offers them, look at `Cancel`, `Not now`,
> `‹ Back to Jobs`, `Show in folder` and `Change jobs folder`.
> **Should:** blue writing, no box round it. Nothing that only moves you, shows
> you something, or backs you out is ever a coloured button.
> **Wrong if:** any of them is filled with colour, or shouts louder than the
> thing the screen is for.

> ### Check 23. One-way things are written in red
> Find `Clear captions`, `Remove it`, `Forget it`, `Close the app`, and
> `Reset demo` if this machine has it.
> **Should:** a plain button with a line round it and red writing inside. Red
> says you cannot take it back. Not filled says it is not why you came here.
> **Wrong if:** any of them is solid red, or is plain blue writing like a
> cancel.

> ### Check 24. A button you cannot use yet says why
> On a job's photographs, before every caption is ticked, look at
> `Build photo pages` and rest the pointer on it.
> **Should:** grey, still readable, still saying what it is, and a few words
> appear telling you what has to happen first.
> **Wrong if:** it is hidden, or it still looks like something you could press,
> or resting on it says nothing.

## The small x on a message

> ### Check 25. The x clears a message
> Put a message on screen: build, or clear captions, or read the
> `Will be saved as` line on the photographs screen. Click the small x in its
> corner.
> **Should:** that message goes, and stays gone while you are on that screen.
> Nothing else changes.
> **Wrong if:** it comes straight back, or the x undoes the thing the message
> was telling you about.

> ### Check 26. A question never has an x
> Open the step that asks you to agree to a cost, the one that asks before
> clearing captions, and the one that asks before resetting the demo.
> **Should:** none of them has an x. The only ways out are the buttons on it.
> **Wrong if:** any question can be closed with an x instead of answered.

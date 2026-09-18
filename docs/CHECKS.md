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

> ### Check 9. `Show what will be sent` puts the log on the screen
> Open Settings, click **`Show what will be sent`**, read it, then click
> **`Copy`** and paste it into anything.
> **Should:** the log text appears on the screen, it names both log files when
> the log has rotated, and what you paste is what you read.
> **Wrong if:** nothing appears to happen, a folder window opens instead, or
> the pasted text is shorter than what is on screen.

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
> **Should:** a loading page says it is closing the copy already open, then it becomes the app.
> **Wrong if:** two copies end up running, it says it could not close the first, or the page never becomes the app.

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
## Sending the log

> ### Check 27. `Send the log to Spenser` sends it, once
> Open Settings, click **`Send the log to Spenser`**, wait for the answer, then
> click it again.
> **Should:** the first says it was sent, the button says `Sending...` while it
> goes and cannot be clicked twice, and the second says one already arrived from
> this computer in the last hour.
> **Wrong if:** nothing on the screen changes, or a failure leaves you with
> nothing to do about it.

> ### Check 28. A log still reaches him with the internet off
> Turn the network off. Click **`Send the log to Spenser`**.
> **Should:** it says the internet may be off, says to try again in a minute,
> and tells you to press `Show what will be sent`, press `Copy`, and paste it
> into an email to the address it names.
> **Wrong if:** it says it was sent, or the message gives you no way through.

## The photographs slice, 18 September 2026

Everything in the next test build that a person can see or do on the
photographs screen, and the update pieces that ship with it. Walk them in this
order: each group leaves the job the way the next one expects.

Use a job with a dozen or so photographs, most of them captioned. Check 38
needs a key in Settings and a job the app is allowed to send photographs from.

**Money.** Only one check here spends: 38, about 5 cents on the key in
Settings. Every other check is free. **Do not press `Generate captions`** in
any of them: opening its window alone writes six sample captions, about 30
cents, before you agree to anything.

**If a check marked "Read this one twice" fails, stop there and tell Spenser.**
Do not carry on to the next one.

**Opening a job**

> ### Check 29. The photographs screen reads at normal zoom
> Set the browser to 100 per cent (Ctrl and 0). Open a job's photographs.
> **Should:** it looks the way it used to at 90 per cent, with as many
> photographs to a row. Only the masthead and the dark bar at the top are a
> little bigger. Jobs and Settings are the size they always were.
> **Wrong if:** you want to zoom out to read it, or another screen changed size.

> ### Check 30. Words fill the box they sit in
> Open Settings, and open a job that asks which folder holds its photographs.
> **Should:** every paragraph runs to the right edge of its box before it wraps.
> **Wrong if:** a paragraph wraps a third of the way across and leaves the rest
> of its box empty.

**The widget**

> ### Check 31. The photographs never cover the widget
> Open a job with plenty of photographs. Look at the bottom row of the widget,
> the one with the counts and the money. Scroll down and back up.
> **Should:** that whole row is always visible, with nothing painted over it.
> **Wrong if:** the first row of photographs covers any part of it.

> ### Check 32. The two buttons share the top row equally
> Look at `Build photo pages` and `Generate captions` in the widget. Do not
> press `Generate captions`.
> **Should:** the same width, filling the row edge to edge with only a hair
> between them, and the photograph-with-a-plus button sits directly under the
> left edge of `Build photo pages`.
> **Wrong if:** one is wider, or there is a gap in the middle of the row.

> ### Check 33. A switched-off button still looks like its own button
> On a job with a caption not yet ticked, look at `Build photo pages`. On a
> job where every photograph has a caption, look at `Generate captions`. Rest
> the pointer on each.
> **Should:** a pale fill with a thin edge in the button's own colour, red for
> Build and blue for Generate, words still readable, and a few words saying why
> it is off. Neither changes size when it switches on.
> **Wrong if:** they are two identical flat grey slabs, or either looks like it
> could be pressed.

**The photographs**

> ### Check 34. Back and Refresh are on every photograph
> Look at the row under any photograph, then under several others.
> **Should:** the tick circle at the left, band circles if Bands is on, then a
> Back circle with a curved arrow, then a Refresh pill with a circular arrow
> and a price such as `~5¢` inside it. The same price on every photograph.
> **Wrong if:** any photograph is missing one of them, or two show different
> prices.

> ### Check 35. Refresh cannot spend where it is not allowed
> Find a job where resting on `Generate captions` says `These photos are demo
> material kept for local testing`. Press Refresh on one photograph.
> **Should:** Refresh is switched off on every photograph, nothing happens, and
> no caption changes. Free.
> **Wrong if:** `Writing captions...` appears, or a caption changes.

**Captions and ticks**

> ### Check 36. A caption you type counts as reviewed
> Type a caption into a photograph that has none, then click somewhere else.
> Then change one word in a caption the AI wrote and click away.
> **Should:** each time, the tick under it turns green on its own. Leave the
> job and come back: still green.
> **Wrong if:** either tick stays empty.

> ### Check 37. A tick needs a caption
> Delete every word from a ticked caption and click away. Rest the pointer on
> its tick.
> **Should:** the tick goes empty and cannot be clicked, and resting on it says
> `Write a caption first`.
> **Wrong if:** a green tick sits under an empty box.

> ### Check 38. Refresh writes one new caption for the price on it
> **Spends money: about 5 cents.** The figure on the pill is the most it can
> cost. On a job the app is allowed to send, press Refresh once on one
> captioned photograph.
> **Should:** no window asks first. The line under the title says
> `Writing captions...`, then that one caption is replaced with new words.
> **Wrong if:** a window opens, more than one caption changes, or it fails and
> nothing says why.

> ### Check 39. The AI's captions wait for your tick. **Read this one twice.**
> Look at the tick under the caption Check 38 just wrote, and under any other
> caption the AI wrote that you have not ticked.
> **Should:** empty, and it stays empty until you click it yourself.
> **Wrong if:** a caption the AI wrote ever ticks itself. That breaks the one
> rule about AI in this app: a person reads everything it writes. **Stop and
> tell Spenser.**

> ### Check 40. The bar counts reviewed, and nothing else.
> With some captions ticked and some not, read the bottom row of the widget.
> Tick one more.
> **Should:** it reads `N of M reviewed`, where M is the photographs in the
> report, and N goes up by one when you tick.
> **Wrong if:** it shows separate counts for the AI and for you, or N does not
> move.

> ### Check 41. Who wrote each caption shows quietly on the photograph.
> Look at a caption you typed in Check 36 and the one Refresh wrote in
> Check 38.
> **Should:** under each caption, small and grey, it says `AI` or `Typed`.
> Editing an AI caption changes it to `Typed`.
> **Wrong if:** nothing says who wrote it, it says the wrong one, or it shouts:
> colour, a box, or anything that competes with the caption.

**Bands**

> ### Check 42. Clicking a band letter shows only that band
> Turn Bands on. Put a few photographs in A and a few in B. Click `A` in the
> widget.
> **Should:** only band A's photographs show and the A is filled black. The
> photograph and page counts under the title do not change.
> **Wrong if:** other photographs still show, or the counts drop to band A's.

> ### Check 43. Clicking it again shows them all
> With A showing, click `A` again. Then click `A`, then `B`. Then turn Bands
> off.
> **Should:** A again shows every photograph. `B` while A is on switches to
> band B. Bands off shows every photograph and hides the letters.
> **Wrong if:** any click leaves photographs hidden that should show.

> ### Check 44. The controls hold their places with Bands on or off
> Note where the tick, Back and Refresh sit under one photograph. Switch Bands
> off, then on.
> **Should:** the band circles vanish and come back, and the tick, Back and
> Refresh do not move at all.
> **Wrong if:** anything on that row slides sideways.

**Clearing and restoring**

> ### Check 45. The job-wide back waits for a clear
> On a job that has never been cleared, rest the pointer on the small curved
> arrow to the right of `Clear captions`.
> **Should:** grey, and resting on it shows nothing. Back on each photograph
> is grey and shows nothing either.
> **Wrong if:** either can be pressed before a clear, or either shows a
> message when greyed.

> ### Check 46. Clear captions takes the ticks, and Build goes off. **Read this one twice.**
> On a job where every caption is ticked and `Build photo pages` is solid red,
> click `Clear captions` and agree.
> **Should:** every caption and every tick goes. `Build photo pages` switches
> off, and resting on it says `Tick every caption you have read first.`
> **Wrong if:** a tick survives under an empty box, or Build stays red for a
> report with no words in it. **Stop and tell Spenser.**

> ### Check 47. Restore cleared captions brings the words back without the ticks
> Straight after the clear, rest on the curved arrow, then click it.
> **Should:** it says `Restore cleared captions`. Every caption comes back word
> for word, every tick stays empty, and the arrow goes grey again.
> **Wrong if:** a caption is missing or changed, or the ticks come back.

> ### Check 48. Restore spares what you changed. **Read this one twice.**
> Clear captions again. Type new words into one photograph and click away. Then
> click `Restore cleared captions`.
> **Should:** your new words stay exactly as you typed them. Every other
> photograph gets its old caption back.
> **Wrong if:** your words are replaced. That is his work lost without a
> question. **Stop and tell Spenser.**

> ### Check 49. Back on one photograph works on its own
> Clear captions once more. Press Back on one photograph only, then rest on it.
> **Should:** only that photograph gets its words back, with its tick empty,
> and its Back stays live so it can be used again.
> **Wrong if:** any other photograph changes, or its tick comes back on.

**Money**

> ### Check 50. The money rounds up to the cent, not the nickel
> After Check 38 has spent, open a job with photographs still uncaptioned and
> read the figure at the right end of the widget's bottom row.
> **Should:** whole cents, rounded up, ending in any digit: `~58¢` or `~$2.88`
> as readily as `~60¢`. On a computer that has never spent on captions, a
> multiple of 5 is right too. From $10 up it shows whole dollars, rounded up:
> `$13`, not `$12.34`.
> **Wrong if:** it shows part of a cent, or it is more than the price on the
> Refresh pill times the number of photographs without a caption.

**Settings and updating**

> ### Check 51. Check now says when it could not check
> Turn the network off. Open Settings and click **`Check now`**.
> **Should:** `Could not check for a new version.`
> **Wrong if:** `You are on the newest version.` The app does not know that.

> ### Check 52. Check now says newest only when it knows
> Network on, nothing newer published. Click **`Check now`**.
> **Should:** `You are on the newest version.`
> **Wrong if:** anything else.

> ### Check 53. Check now offers the update beside it
> With a newer version published, click **`Check now`**.
> **Should:** `Version X is available.` and an **`Update available`** button
> appears beside `Check now`. Clicking it opens the same box as the
> `Update available` button at the top of the screen.
> **Wrong if:** the sentence sends you to the top of the screen, no button
> appears, or it opens something different.

> ### Check 54. The update box says less
> Open the update box.
> **Should:** `Update to version X?`, then one paragraph: you are on version Y,
> the download size, `The app closes itself and opens again as a new version.
> Your settings remain the same.` Then `Update now` and `Not now`. The words
> run the full width of the box.
> **Wrong if:** there is a paragraph about checking the download, or the words
> stop a third of the way across.

> ### Check 55. A stopped update writes its reason in the log
> Click `Update now`, and click `Cancel` while it says `Downloading`. Then open
> Settings and click **`Show what will be sent`**.
> **Should:** the box says `The update was stopped. Nothing has changed.` Near
> the end of the log is a line saying `update did not finish` with that same
> sentence. The app is still on the old version.
> **Wrong if:** the log has no such line.

> ### Check 56. The loading page says the app is not answering
> Click `Close the app`. In File Explorer open your user folder, then
> `.rrf-app-cache`, and double-click `starting.html`. Touch nothing for half a
> minute.
> **Should:** after about 20 seconds it says `Roy R. Fisher is not answering.`,
> `Close this tab and double-click the icon.`, and the line about sending
> Spenser the window.
> **Wrong if:** it says the app has probably opened in another tab, or talks
> about how some computers are set up.

## The photographs batch, 0.7.6.4, 18 September 2026

What changed after his 0.7.6.3 results. Checks 57 and 58 each refresh one
caption, which spends a few cents on the key in Settings. The rest are free.

> ### Check 57. Refresh says Refreshing caption on the photograph
> On one captioned photograph, click the refresh button, the one with the price on it.
> **Should:** `Refreshing caption` sits over that picture while it works, and goes away when the new caption arrives.

> ### Check 58. Back undoes a Refresh
> Straight after Check 57, click the back arrow on the same photograph.
> **Should:** the caption from before the Refresh comes back.

> ### Check 59. The Writing captions bar runs the length of its line
> Look at `Writing captions · N of N written` under the title.
> **Should:** its bar runs to the end of that line, not a short stub.

> ### Check 60. The title row stays at the top
> Scroll down a long page of photographs.
> **Should:** the title and the widget stay at the top, with a thin red line under them across the whole screen.

> ### Check 61. A moved photograph stays in the filtered view
> Switch Bands on, click **`A`** in the widget, then click **`B`** on one of the photographs showing.
> **Should:** it stays on screen, now in B, until you click A again or pick another letter.

> ### Check 62. The done tick is a darker green
> Mark every photograph reviewed.
> **Should:** the `reviewed` pill turns a darker green than before, easy to read.

> ### Check 63. A switched-off button keeps its colour, faded
> Open a job where `Build photo pages` or `Generate captions` is switched off, and rest the pointer on it.
> **Should:** Build is a faded red, Generate a faded blue, and resting on it says why it is off.

> ### Check 64. AI or Typed sits in the photograph's upper left corner
> Look at any captioned photograph.
> **Should:** `AI` or `Typed` sits in the upper left of the picture, and the caption line under it is not pushed down.

> ### Check 65. Check now answers to the right
> In Settings, click **`Check now`**.
> **Should:** the answer appears on the same row, to the right of the button, not under it.

> ### Check 66. The whole update happens in the version card
> Needs a version newer than 0.7.6.4 on offer. Click **`Update available`** at the top, then `Update now`.
> **Should:** Settings opens and the question, the progress and `Starting...` all appear inside `The version you are running`, with nothing above the cards. The version is said once, not twice.

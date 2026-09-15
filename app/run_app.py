"""Start the Roy R. Fisher app: check the package, pick a port, then serve.

The order below is the whole point of this file, so it is worth stating once.
Everything up to the uvicorn import uses the standard library only, because a
package whose wheels went missing must still be able to say so in a sentence.
The old thirteen-line version imported uvicorn at the top, which meant an
incomplete unzip produced an ImportError traceback before any of our code could
speak.

Both platforms take this path. The .bat and the .command are thin shims that
change to this folder and run this file, so the port check and the failure
message are written once rather than once in batch and once in bash.
"""
import sys
import threading
import webbrowser
from pathlib import Path

SERVER = Path(__file__).resolve().parent / "server"
sys.path.insert(0, str(SERVER))

import packaging  # noqa: E402  standard library only
import splash  # noqa: E402  standard library only
import startup  # noqa: E402  standard library only
import tell  # noqa: E402  standard library only

# Two folders, and they are the same one in a development checkout.
#
# PROGRAM holds VERSION, MANIFEST, app/ and python/, and is what the package
# check verifies. HOME is the version folder Mark sees: in a package it holds
# PROGRAM beside the launcher, the readme and the practice jobs, and it is what
# the sibling scan compares against other installed versions.
PROGRAM = Path(__file__).resolve().parents[1]
HOME = PROGRAM.parent if PROGRAM.name == packaging.PROGRAM_DIR else PROGRAM

# Kept so nothing that already reads ROOT has to change its meaning: it is the
# folder the manifest describes.
ROOT = PROGRAM

# How long after a successful start a version has to survive before it is
# recorded as the last one that worked. Long enough that a lazily failing
# import or a crash on first work has already happened, short enough that Mark
# has not closed the window. The record is evidence for Spenser; nothing
# consumes it automatically and nothing rolls back on its own.
GOOD_AFTER_SECONDS = 20.0

# How long the app waits, after it is up, for the loading page to say it got
# there, before it opens a tab of its own.
#
# The page asks every half second, so when it is not blocked it has almost
# always spoken before the app has finished answering, and this wait ends the
# moment it does. Nobody sits through it in the ordinary case.
#
# It is waited out in two cases and it is right to be short in both. One is the
# blocked page, where five seconds is added to a start he is already watching a
# bar for, and at the end of it the app is in front of him. The other is a
# browser that took longer to draw the page than the app took to start, which
# is indistinguishable from blocked and costs one spare tab. Waiting longer
# would trade his time for that tab, and his time is worth more.
HANDOVER_SECONDS = 5.0


def _record_last_good(version: str) -> None:
    """Written from the server process, never from a launcher that has exited.

    A launcher that opens the browser and returns cannot witness anything
    afterwards, so it could only record a success it did not see. This runs
    here, in the process that is actually serving, so the timer firing is
    itself the evidence that the process was still alive.
    """
    try:
        import datetime

        import appversion
        appversion.record(version, datetime.datetime.now().isoformat(timespec="seconds"))
    except Exception as exc:
        # Diagnostic bookkeeping must never take the app down. If it cannot be
        # written, the app still works and Spenser reads one fewer thing.
        try:
            import applog
            applog.note("last-good record failed", version=version, error=str(exc))
        except Exception:
            pass


def _start() -> int:
    version = packaging.version_of(ROOT)

    # The order below changed on 2026-09-08, and the reason is the whole point
    # of it. The package check hashes every file in the package and is the
    # slowest thing here. It used to run first, with nothing on screen, so
    # double-clicking the icon did nothing visible for several seconds.
    # Spenser: "Can we make a loading screen?" A loading screen has to open
    # before the slow work, not after it, so the cheap checks run first, the
    # screen goes up, and the hashing happens behind it.
    #
    # Nothing was made less safe by moving it. The two checks now above it use
    # the standard library only and touch nothing, and the file that records a
    # running app is still written after the check, so writing it still cannot
    # invalidate the package. Its name is deliberately not repeated here: a
    # test asserts the order by where the symbol first appears in this file,
    # and prose that names it early reads as the call happening early.

    # 1. Is anything already running, here or beside us?
    #
    #    Both cases are one case, since 0.7.1. A different version beside us
    #    used to be refused with "close that window first", which is an
    #    instruction nobody can follow: there has been no window since 0.6.5.
    #    The same version in this folder used to be opened instead of started,
    #    which is how Mark spent an evening in front of a two-hour-old build on
    #    2026-09-14. Four builds that day all called themselves 0.7.0, so
    #    "it is already running" is not something the version number can
    #    establish. Whatever is running is stopped, and this copy takes over.
    running = startup.copies_running(HOME)

    # 2. Ask the operating system for a port. Only the asking: the file that
    #    records it is written further down, after the package check.
    port = startup.free_port()

    # 3. Say the click landed, before the slow part, and say which slow part it
    #    is. The page replaces itself with the app the moment the app answers,
    #    when the browser lets it, and tells the app on its way past so that
    #    step 6 below does not open a second tab beside it.
    #
    #    What is recorded here is only whether the browser was given the page
    #    at all. False means there is nobody who could ever hand over, so step
    #    6 opens the app without waiting for a message that cannot come.
    saying = None
    patience = None
    if running:
        saying = ("Closing the copy that is already open, then starting "
                  "version %s." % version)
        patience = int(splash.GIVE_UP_SECONDS + startup.STOP_TIMEOUT)
    showing = splash.show(port, version, saying=saying, patience=patience)

    # 4. Stop what is running, then carry on. `tell.say` reaches the console on
    #    the Mac; on Mark's machine there is none, and the loading page above is
    #    what he is reading.
    try:
        startup.stop_the_running_copies(running, say=tell.say)
    except startup.StartupRefused as exc:
        tell.problem(exc.message)
        return 3

    # 5. Is this package whole?
    #
    #    Skipped in the development checkout, which has no manifest and never
    #    will. Deciding that by the presence of app/tests rather than by the
    #    absence of the manifest matters: the absence of a manifest is exactly
    #    what a half-finished unzip looks like, so it must stay an error in
    #    anything shaped like a package. Mark's copy has no app/tests, so his
    #    still fails closed.
    if packaging.is_checkout(ROOT):
        tell.say("Development checkout: skipping the package check.")
    else:
        try:
            packaging.verify(ROOT)
        except packaging.PackageDamaged as exc:
            tell.problem(exc.message)
            return 2

    startup.write_runtime(HOME, port, version)

    tell.say("Starting Roy R. Fisher %s." % version)
    tell.say("Leave this window open while you work.")
    tell.say(startup.STOP_INSTRUCTION)
    tell.say("")

    # 6. Open the browser only once the app has really answered, and answered
    #    as this version. 7. Then start the clock on the last-good record.
    def when_up():
        if startup.wait_until_answering(port, version):
            # One tab, not two.
            #
            # This was unconditional from 2026-09-14, because there was no way
            # from here to find out whether the loading page had managed to
            # hand over. On Mark's Windows machine it had not: a page loaded
            # from a file on disk may be barred from asking a server on the
            # same computer anything, and Edge barred it, so the app was
            # running and nobody was looking at it. Opening every time cost a
            # spare tab whenever the page did work, and Spenser has watched it
            # work, so both happen.
            #
            # There is a way now. The page announces itself on its own route on
            # the way past, so the silence that used to mean "no idea" means
            # "nothing reached us", and that is exactly the case this tab is
            # for. A page that is blocked cannot tell anybody anything, which
            # is why the absence of a message, and not any message, is what
            # opens the browser here.
            if not (showing and startup.wait_for_the_loading_page(HANDOVER_SECONDS)):
                webbrowser.open("http://%s:%d" % (startup.HOST, port))
            threading.Timer(GOOD_AFTER_SECONDS, _record_last_good, (version,)).start()
        else:
            # 8. Plain words, not a traceback. The server thread is still up,
            #    so this cannot exit the process itself; it says what it knows
            #    and closing the window ends it.
            tell.problem(startup.failure_report(HOME, port, version))

    # Tidy the app's own thumbnail cache, off the startup path. Bounded, and
    # it only ever deletes inside the cache the app writes: a legacy
    # `.rrf-thumbs` folder inside one of Mark's jobs is never reached by it.
    def tidy_cache():
        try:
            import thumbcache
            thumbcache.prune()
        except Exception as exc:
            # Housekeeping must never take the app down or say anything about
            # itself on screen. Nothing depends on it having run.
            try:
                import applog
                applog.note("cache tidy failed", error=str(exc))
            except Exception:
                pass

    # Look once for a newer version, off the startup path and silently.
    #
    # Approved 2026-08-28. Looking is not updating: nothing downloads, nothing
    # installs, and nothing appears on screen unless a newer version is
    # actually being offered. It is one request for one small public file, and
    # it is what makes "he is told and he chooses" possible at all.
    #
    # Silent on failure on purpose. No internet, a bucket that is down, or a
    # slow morning must look exactly like there being no update, because none
    # of those are things Mark can act on.
    def look_for_an_update():
        try:
            import updates
            updates.look(ROOT)
        except Exception as exc:
            # Same rule as the cache tidy above. Nothing depends on this having
            # run, and it may never take the app down.
            try:
                import applog
                applog.note("update check failed", error=str(exc))
            except Exception:
                pass

    import uvicorn          # the first third-party import in the whole file

    # 10. Only now. B15, proven on Spenser's Windows machine on 2026-09-15:
    #     these three used to start on the line above the import, and that is
    #     what killed every version the first time it ran.
    #
    #     On a machine that has never run this version there is no compiled
    #     cache, so these three have to compile hundreds of files. That takes
    #     long enough that the uvicorn import chain reached `dataclasses` while
    #     one of them still had `typing` half built, read the half-built module
    #     and died: "partially initialized module 'typing' has no attribute
    #     'ClassVar'". No window, no message. The second run found a warm cache
    #     and worked, and so did every run after it, which is why it looked
    #     random for a week.
    #
    #     Nothing between the old place and this one needed them. `when_up`
    #     waits for the server to answer, so it only has to be running before
    #     `uvicorn.run` below, not before the import.
    threading.Thread(target=tidy_cache, daemon=True).start()
    threading.Thread(target=look_for_an_update, daemon=True).start()
    threading.Thread(target=when_up, daemon=True).start()

    try:
        # Quiet. uvicorn's own INFO lines announced a process id, a bind
        # address and every request, which is real server output in a window
        # a person has been told is not a piece of software. Warnings and
        # errors still print, because those are the ones worth photographing
        # and sending to Spenser.
        uvicorn.run("main:app", host=startup.BIND_HOST, port=port,
                    log_level="warning", access_log=False)
    finally:
        # 9. The record of a running app goes when the app stops.
        #
        #    Measured 2026-08-22, and narrower than it first looked. Control-C
        #    reaches here and the file goes. A kill does not, and neither,
        #    almost certainly, does closing the console window on Windows,
        #    which is a CTRL_CLOSE_EVENT rather than an interrupt and is the
        #    way Mark is told to stop the app. Handling that needs a Windows
        #    console handler and a Windows machine to prove it on, so it is
        #    written up rather than guessed at.
        #
        #    Nothing depends on this having run. A file left behind names a
        #    port, the next launch asks that port whether our version is
        #    answering, and a dead port answers nothing. The installer asks the
        #    same question before it copies. So the worst case is a stale file
        #    that everything already treats as meaningless.
        startup.clear_runtime(HOME)
    return 0


def _where_the_log_is() -> str:
    """Named in the message, because he is being asked to send it."""
    try:
        import applog
        return str(applog.log_file())
    except Exception:
        return ".rrf-app.log"


def main() -> int:
    """`_start`, with nothing left able to die in silence.

    The launcher spoke for two failures it knew by name, a damaged package and
    a server that never answered, and let everything else fall out of the
    bottom. On the Mac that prints a traceback. On Mark's machine the shortcut
    runs `pythonw.exe`, which has no console, so it printed into nowhere: no
    window, no message, nothing. B15 lived in that gap for a week.

    So anything unexpected now goes to both places `tell` knows about. The log
    gets the whole traceback, because that is the thing Spenser can be sent
    afterwards. The person in front of the machine gets a message box with the
    one line that matters and what to do about it.

    Control-C is not one of these. It is how the app is stopped on purpose on
    the Mac, and a box asking him to send a log would be wrong.
    """
    try:
        return _start()
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        import traceback
        named = "%s: %s" % (type(exc).__name__, exc)
        try:
            import applog
            applog.note("the app could not start", error=named,
                        traceback=traceback.format_exc())
        except Exception:
            # The log is the better record, but it may not become the reason
            # the message below is never shown.
            pass
        tell.problem(
            "Roy R. Fisher could not start.\n"
            "\n"
            "  %s\n"
            "\n"
            "Start it again. If it happens twice, send Spenser this message\n"
            "and the file %s." % (named, _where_the_log_is()))
        return 4


if __name__ == "__main__":
    sys.exit(main())

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
import startup  # noqa: E402  standard library only

ROOT = Path(__file__).resolve().parents[1]

# How long after a successful start a version has to survive before it is
# recorded as the last one that worked. Long enough that a lazily failing
# import or a crash on first work has already happened, short enough that Mark
# has not closed the window. The record is evidence for Spenser; nothing
# consumes it automatically and nothing rolls back on its own.
GOOD_AFTER_SECONDS = 20.0


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
    except Exception:
        # Diagnostic bookkeeping must never take the app down. If it cannot be
        # written, the app still works and Spenser reads one fewer thing.
        pass


def main() -> int:
    version = packaging.version_of(ROOT)

    # 1. Is this package whole? Before any third-party import, and before
    #    runtime.json is created or touched.
    #
    #    Skipped in the development checkout, which has no manifest and never
    #    will. Deciding that by the presence of app/tests rather than by the
    #    absence of the manifest matters: the absence of a manifest is exactly
    #    what a half-finished unzip looks like, so it must stay an error in
    #    anything shaped like a package. Mark's copy has no app/tests, so his
    #    still fails closed.
    if packaging.is_checkout(ROOT):
        print("Development checkout: skipping the package check.")
    else:
        try:
            packaging.verify(ROOT)
        except packaging.PackageDamaged as exc:
            print(exc.message)
            return 2

    # 2. Is a different version already running beside this one?
    try:
        startup.refuse_if_another_version_runs(ROOT)
    except startup.StartupRefused as exc:
        print(exc.message)
        return 3

    # 3. Is this same version already running? Then just show it.
    existing = startup.already_running_here(ROOT, version)
    if existing:
        print("Roy R. Fisher %s is already running. Opening it." % version)
        webbrowser.open("http://%s:%d" % (startup.HOST, existing))
        return 0

    # 4. Ask the operating system for a port, and remember which one.
    port = startup.free_port()
    startup.write_runtime(ROOT, port, version)

    print("Starting Roy R. Fisher %s." % version)
    print("Leave this window open while you work.")
    print(startup.STOP_INSTRUCTION)
    print()

    # 5. Open the browser only once the app has really answered, and answered
    #    as this version. 6. Then start the clock on the last-good record.
    def when_up():
        if startup.wait_until_answering(port, version):
            webbrowser.open("http://%s:%d" % (startup.HOST, port))
            threading.Timer(GOOD_AFTER_SECONDS, _record_last_good, (version,)).start()
        else:
            # 7. Plain words, not a traceback. The server thread is still up,
            #    so this cannot exit the process itself; it says what it knows
            #    and closing the window ends it.
            print(startup.failure_report(ROOT, port, version))

    threading.Thread(target=when_up, daemon=True).start()

    import uvicorn          # the first third-party import in the whole file
    try:
        # Quiet. uvicorn's own INFO lines announced a process id, a bind
        # address and every request, which is real server output in a window
        # a person has been told is not a piece of software. Warnings and
        # errors still print, because those are the ones worth photographing
        # and sending to Spenser.
        uvicorn.run("main:app", host=startup.BIND_HOST, port=port,
                    log_level="warning", access_log=False)
    finally:
        # 8. The record of a running app goes when the app stops. A crash that
        #    never reaches here leaves one behind, and the next launch handles
        #    that by probing the port rather than by trusting the file.
        startup.clear_runtime(ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())

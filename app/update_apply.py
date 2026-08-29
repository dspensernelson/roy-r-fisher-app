"""Finish an update after the app that started it has gone.

Windows will not let a running program replace its own files, so the app
cannot install an update over itself. It downloads the package, checks it
twice, starts this, and exits. This waits for it to be gone and then does the
installing.

**It runs out of the new package, not the old one.** The app starts it with the
new package's own `python.exe`, so once this is running nothing in the old
version folder is held open. That is what leaves `install_windows.py` free to
copy over it and free to prune it.

**It has its own console window.** That window is the only place a plain
failure message can land once the app has closed, and it stays open on failure
so there is something to read. The pilot decision to keep the console visible
applies here at least as much as it does to the launcher.

**It never deletes the folder it is standing in.** The scratch folder is
cleared at the start of the next attempt instead. One rule, in one place,
rather than a tidy-up that can only sometimes run.

**Whatever happens, the Desktop icon works.** If the wait times out, if the
install refuses, if anything at all goes wrong, the previous version is still
installed and the icon still points at it. Every failure message here says so,
because Mark is remote, he will not debug anything, and the one thing he can
always do is double-click that icon.

Standard library only, like `install_windows.py` and `startup.py` beside it.
"""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "server"))

import install_windows as installer  # noqa: E402  standard library only

# How long to wait for the app that started this to actually go. Generous: it
# is closing a web server and Windows takes its own time about a console. Long
# enough that a slow machine is not mistaken for a stuck one, short enough that
# a genuinely stuck one is reported while Mark is still watching.
WAIT_SECONDS = 90.0
POLL_SECONDS = 1.0

# Said after every failure, because it is the only sentence that matters.
# What it can actually see: the previous version's folder was never touched,
# because installing copies into a new folder beside it and refuses before
# copying anything at all. Whether that version *works* is not something this
# can observe, so it does not say so.
STILL_WORKS = (
    "The version you had is still installed and was not changed.\n"
    "Start it from the Roy R. Fisher icon on your Desktop.")


def wait_for_the_app_to_close(home, seconds=WAIT_SECONDS, sleep=time.sleep,
                              now=time.monotonic) -> str:
    """Wait until nothing is serving. Returns the version still up, or empty.

    Waits on `install_windows.something_running`, which is the exact condition
    the install itself refuses on, rather than on a proxy for it. Anything else
    would mean the rule the installer enforces and the rule this obeys were two
    readings of one line.
    """
    deadline = now() + seconds
    while True:
        answering = installer.something_running(home)
        if not answering:
            return ""
        if now() >= deadline:
            return answering
        sleep(POLL_SECONDS)


def start_new_version(launcher, spawn=None) -> bool:
    """Open the version that was just installed.

    A `.bat` cannot be handed straight to CreateProcess on Windows, so it goes
    through `cmd.exe`, in its own console, the same way the Desktop icon opens
    it. Failing to start it is not a failed update: the update worked, and the
    icon on his Desktop already points at the new version.
    """
    launcher = Path(launcher)
    if spawn is None:
        spawn = subprocess.Popen
    command = ["cmd.exe", "/c", str(launcher)]
    options = {"cwd": str(launcher.parent)}
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    if flags:
        options["creationflags"] = flags
    try:
        spawn(command, **options)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def hold_the_window(read=None) -> None:
    """Keep the console open so the message on it can be read.

    Wrapped, because a process started without a console has no stdin and
    asking for a line raises. Failing to pause must not turn a reported failure
    into a traceback on top of it.
    """
    if read is None:
        read = input
    try:
        read("Press Enter to close this window. ")
    except (EOFError, OSError, KeyboardInterrupt):
        pass


def apply(home=None, source=None, out=print, sleep=time.sleep,
          now=time.monotonic, spawn=None) -> int:
    """Do the install. Returns the exit code, and never raises.

    `source` is the package to install and is normally left alone: this file
    lives inside the package it installs, so `install_windows.install()` finds
    the right tree on its own and there is no path for a caller to get wrong.
    A test passes one explicitly.
    """
    home = installer.install_home() if home is None else Path(home)

    out("Roy R. Fisher update")
    out("")
    out("Waiting for the app to close...")
    still_up = wait_for_the_app_to_close(home, sleep=sleep, now=now)
    if still_up:
        out("")
        out("Roy R. Fisher %s is still running, so the update was not "
            "installed." % still_up)
        out("Close its window and run the update again.")
        out("")
        out(STILL_WORKS)
        return 1

    try:
        done = installer.install(source)
    except installer.InstallRefused as exc:
        out("")
        out(exc.message)
        out("")
        out(STILL_WORKS)
        return 1
    except Exception as exc:
        # Anything at all. This process is the last thing standing between Mark
        # and a closed app, so it says something readable rather than printing
        # a traceback nobody can act on.
        out("")
        out("The update did not finish:")
        out("    %s" % exc)
        out("")
        out(STILL_WORKS)
        return 1

    out("")
    out("Updated to version %s." % done["version"])
    out("  Installed in: %s" % done["installed_to"])
    out("  Start it from: %s" % done["icon"])
    if done["previous"]:
        out("")
        out("  The version you had is still here and still works.")
        out("  If this one gives you trouble, close it and run:")
        out("      %s" % (Path(done["home"]) / installer.ROLLBACK_NAME))
    out("")
    out("Opening Roy R. Fisher %s..." % done["version"])
    launcher = Path(done["installed_to"]) / installer.LAUNCHER_NAME
    if not start_new_version(launcher, spawn=spawn):
        out("")
        out("It could not be opened from here, which does not undo the "
            "update.")
        out("Start it from the Roy R. Fisher icon on your Desktop.")
    return 0


def main() -> int:
    code = apply()
    if code:
        hold_the_window()
    return code


if __name__ == "__main__":
    sys.exit(main())

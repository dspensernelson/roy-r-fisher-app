"""Put this package where it lives, and make one thing on the Desktop start it.

The same action installs and updates. Mark unzips a folder, double-clicks
`Install or update Roy R. Fisher.bat`, and afterwards there is one icon on his
Desktop that starts the newest version. Doing it again with a newer package
replaces the icon's target and leaves the old version in place.

Why a batch shim over a Python file rather than an installer: nothing but
Python runs on his machine, an .msi or a signed .exe cannot be built or tested
from the Mac this is developed on, and an unsigned installer is a worse
SmartScreen prompt than an unsigned .bat. The .bat is three lines; everything
that can be got wrong is here, where it can be tested.

Three rules shape the rest.

His work is never touched. Every file the app owns lives in his home folder,
outside any version folder, so replacing the app cannot reach the key, the
jobs folder, the settings, the usage history, the classifications, or a single
document. This module copies into a version folder and nowhere else.

The previous version survives. Versions install side by side under one parent
and the old one is never overwritten, so a version that fails is undone by
starting the previous one rather than by repairing anything.

It refuses rather than half-finishing. A running app, a damaged package, or a
destination it cannot write to all stop it before anything is copied.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "server"))

import packaging  # noqa: E402  standard library only
import startup  # noqa: E402  standard library only

# The folder every version installs under. One name, so the versions are
# siblings and the launcher's existing single-instance check sees them.
PRODUCT = "Roy R. Fisher"

# How many versions to keep. The newest is what the icon starts and the one
# before it is the way back; a third is slack for the case where he notices a
# problem a version late. Older than that is disk he cannot use.
KEEP_VERSIONS = 3

SHORTCUT_NAME = "Roy R. Fisher.lnk"
FALLBACK_NAME = "Roy R. Fisher.bat"
LAUNCHER_NAME = "Start Roy R. Fisher.bat"
ROLLBACK_NAME = "Start previous version.bat"


class InstallRefused(Exception):
    """A reason not to install, already worded the way Mark should read it."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# ------------------------------------------------------------- where ------
def install_home() -> Path:
    """The parent folder every version lives under.

    LOCALAPPDATA, not Program Files: writing there needs an administrator and
    Mark is not one on every machine he might use. Not the Desktop either,
    which is where the unzipped copy already is and where a second copy would
    be one more thing to tidy.

    RRF_INSTALL_HOME overrides, for tests, the same way RRF_KEY_FILE already
    does for the key.
    """
    override = os.environ.get("RRF_INSTALL_HOME")
    if override:
        return Path(override)
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / PRODUCT
    # Not Windows, or an unusual account. The home folder always exists and is
    # always writable, so this is a working answer rather than a refusal.
    return Path.home() / ("." + PRODUCT.replace(" ", "-").lower())


def desktop_folder() -> Path:
    """Where his Desktop actually is.

    OneDrive moves it. On a machine with Backup turned on the real Desktop is
    `%USERPROFILE%\\OneDrive\\Desktop`, and the old path still exists but is not
    what he looks at, so an icon written there is invisible to him. The
    redirected one is preferred when it is there.
    """
    override = os.environ.get("RRF_DESKTOP")
    if override:
        return Path(override)
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    for candidate in (home / "OneDrive" / "Desktop", home / "Desktop"):
        if candidate.is_dir():
            return candidate
    return home / "Desktop"


def version_folders(home: Path) -> list:
    """Installed versions, newest first, by version number and not by name."""
    try:
        found = [p for p in home.iterdir() if p.is_dir()]
    except OSError:
        return []
    return sorted(found, key=lambda p: (packaging.version_numbers(p.name), p.name),
                  reverse=True)


# ------------------------------------------------------- refusing early ----
def something_running(home: Path) -> str:
    """The version currently serving out of one of these folders, or empty.

    Asks each installed version the same question the launcher asks: is
    something answering on the port this folder recorded, and is it us. A
    folder with a stale runtime.json answers nothing and is not a reason to
    stop.

    Public because the update handoff waits on exactly this condition. It used
    to be private and the waiting code reached in for it, which meant the rule
    the installer enforces and the rule the waiting obeyed were the same line
    read two ways.
    """
    for folder in version_folders(home):
        recorded = startup.read_runtime(folder)
        port = recorded.get("port")
        if not isinstance(port, int):
            continue
        answering = startup.ask_version(port)
        if answering:
            return answering
    return ""


def _refuse_if_anything_is_running(home: Path) -> None:
    """No copying over a version that is serving."""
    answering = something_running(home)
    if answering:
        raise InstallRefused(
            "Roy R. Fisher %s is running.\n"
            "Close its window, then run this again." % answering)


def _check_package(source: Path) -> str:
    """The package must be whole before any of it is copied."""
    # The manifest describes `program/`, so that is what is checked, while the
    # folder being copied is the one above it.
    inner = packaging.program_dir(source)
    try:
        packaging.verify(inner)
    except packaging.PackageDamaged as exc:
        raise InstallRefused(exc.message)
    version = packaging.version_of(inner)
    if not version:
        raise InstallRefused(
            "This folder does not say which version it is, so it cannot be "
            "installed. Unzip the package again.")
    return version


# ------------------------------------------------------------ copying -----
def _copy_version(source: Path, target: Path) -> None:
    """Replace this version's folder with this package, and nothing else.

    Written beside the destination and moved into place, so an interrupted
    copy cannot leave a half-installed version that the launcher would then
    try to verify and start.
    """
    staging = target.with_name(target.name + ".installing")
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    shutil.copytree(
        source, staging,
        ignore=shutil.ignore_patterns(startup.RUNTIME_NAME,
                                      *packaging.NOISE_DIRS, *packaging.NOISE_FILES))
    if target.exists():
        # Same version installed twice. The old copy goes only once the new one
        # is complete beside it.
        shutil.rmtree(target)
    staging.rename(target)


def _prune(home: Path, keep: int, protect: Path) -> list:
    """Delete the oldest versions, never the newest ones and never this one."""
    removed = []
    for folder in version_folders(home)[keep:]:
        if folder.resolve() == protect.resolve():
            continue
        try:
            shutil.rmtree(folder)
            removed.append(folder.name)
        except OSError:
            continue
    return removed


# ---------------------------------------------------------- the icon ------
def _write_rollback(home: Path, previous: str) -> Path:
    """One click that starts the version before this one.

    A file rather than a sentence in a readme, because the moment he needs it
    is the moment the new version is not working and reading is the last thing
    he wants to do.

    The version it starts is written in at install time, when the installer
    already knows which one it is. Working it out in batch would mean sorting
    folder names, and `dir /o-n` sorts text: it would put `0.9.0` above
    `0.10.0` and send him back to the wrong version. It is rewritten by every
    install, which is when it matters.
    """
    script = home / ROLLBACK_NAME
    # Built by joining lines rather than by formatting, because the text is
    # batch and batch is full of per-cent signs.
    if previous:
        lines = [
            "@echo off",
            "REM Starts the version you had before the newest one, for when a new",
            "REM version does not work. Nothing is uninstalled, and nothing of",
            "REM yours moves: your key, your jobs folder, your settings and your",
            "REM documents are not kept in here.",
            'cd /d "%~dp0"',
            "echo Starting Roy R. Fisher " + previous,
            'call "' + previous + '\\' + LAUNCHER_NAME + '"',
            "",
        ]
    else:
        lines = [
            "@echo off",
            "echo Only one version of Roy R. Fisher is installed, so there is",
            "echo nothing to go back to.",
            "pause",
            "",
        ]
    script.write_text("\r\n".join(lines), encoding="utf-8")
    return script


def _remove_stale(path: Path) -> None:
    """Take away one of our own leftovers. Never raises: a Desktop that will
    not let go of a file is not a reason to fail an install."""
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


def _make_shortcut(target_launcher: Path, desktop: Path) -> str:
    """One icon on the Desktop that starts the newest version, with no window.

    A real .lnk when PowerShell will make one, because that is what an icon on
    a Windows Desktop looks like. A .bat when it will not: some machines have
    PowerShell locked down by policy, and an icon that works and looks plain is
    better than no icon at all.

    **It points at `pythonw.exe`, not at the .bat.** Changed 2026-09-03. A .bat
    always opens a console, even one that closes again straight away, and that
    black window was the first thing anybody saw every single time they started
    the app. `pythonw.exe` is the same Python sitting beside `python.exe` in the
    package, built to run without one. Going straight to it means there is no
    window at any point, not even a flash.

    Nothing is lost by it. `app/server/tell.py` puts a failure in a message box
    when there is no console to print to, and in the log either way, which is
    the piece that had to exist before this was safe to do.

    Returns what was written, for the message at the end.
    """
    desktop.mkdir(parents=True, exist_ok=True)
    link = desktop / SHORTCUT_NAME
    version_folder = target_launcher.parent
    pythonw = version_folder / "program" / "python" / "pythonw.exe"
    entry = version_folder / "program" / "app" / "run_app.py"
    # Windows takes an icon from whatever the shortcut points at, and what it
    # points at is now Python, so without this the firm gets Python's logo on
    # its Desktop. The .ico is the app's own three bars, the same shape the
    # masthead draws, and it ships inside the package.
    icon = version_folder / "program" / "app" / "data" / "rrf.ico"
    script = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%s');"
        "$s.TargetPath = '%s';"
        "$s.Arguments = '\"%s\"';"
        "$s.WorkingDirectory = '%s';"
        "$s.IconLocation = '%s';"
        "$s.Description = 'Roy R. Fisher';"
        "$s.Save()" % (link, pythonw, entry, version_folder, icon))
    try:
        done = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, timeout=60)
        if done.returncode == 0 and link.exists():
            # One icon, not two. The fallback below already removes a stale
            # .lnk when it takes over; this is the other half of that, and its
            # absence is why Spenser ended up with two on 2026-09-03. A
            # leftover .bat points at one version folder, and the installer
            # keeps only the newest few, so it dies the moment that version is
            # pruned and leaves an icon that does nothing.
            _remove_stale(desktop / FALLBACK_NAME)
            return str(link)
    except (OSError, subprocess.SubprocessError):
        pass

    fallback = desktop / FALLBACK_NAME
    fallback.write_text(
        "@echo off\r\n"
        'cd /d "%s"\r\n'
        'call "%s"\r\n' % (target_launcher.parent, target_launcher.name),
        encoding="utf-8")
    # Both would be confusing. The stale .lnk goes if it is there.
    try:
        if link.exists():
            link.unlink()
    except OSError:
        pass
    return str(fallback)


# ------------------------------------------------------------- doing it ---
def install(source: Path = None) -> dict:
    """Install or update, from the package this file is sitting in."""
    # The whole unzipped folder, which is one level above `program/`, because
    # the launcher, the readme and the practice jobs all have to travel too.
    source = Path(source) if source else HERE.parents[1]
    version = _check_package(source)

    home = install_home()
    _refuse_if_anything_is_running(home)
    try:
        home.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise InstallRefused(
            "This computer would not let the app be installed into:\n"
            "    %s\n"
            "Send Spenser this window." % home)

    before = [p.name for p in version_folders(home)]
    target = home / version
    updating = target.name in before or bool(before)

    try:
        _copy_version(source, target)
    except OSError as exc:
        raise InstallRefused(
            "Copying the app into place did not finish:\n"
            "    %s\n"
            "Nothing of yours was changed. Send Spenser this window." % exc)

    launcher = target / LAUNCHER_NAME
    icon = _make_shortcut(launcher, desktop_folder())
    # The version to fall back to is the newest one that is not this one.
    earlier = [n for n in before if n != version]
    _write_rollback(home, earlier[0] if earlier else "")
    removed = _prune(home, KEEP_VERSIONS, target)

    return {"version": version, "installed_to": str(target), "icon": icon,
            "home": str(home), "updated": updating,
            "previous": [n for n in before if n != version],
            "removed": removed}


def main() -> int:
    print("Roy R. Fisher")
    print()
    try:
        done = install()
    except InstallRefused as exc:
        print(exc.message)
        print()
        return 1

    print("%s version %s." % ("Updated to" if done["updated"] else "Installed",
                              done["version"]))
    print()
    print("  Installed in: %s" % done["installed_to"])
    print("  Start it from: %s" % done["icon"])
    if done["previous"]:
        print()
        print("  The version you had is still here and still works.")
        print("  If this one gives you trouble, close it and run:")
        print("      %s" % (Path(done["home"]) / ROLLBACK_NAME))
    if done["removed"]:
        print()
        print("  Removed old versions: %s" % ", ".join(done["removed"]))
    print()
    print("You can delete the unzipped folder you ran this from.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Learning that a newer version exists, fetching it, and handing it over.

Approved by Spenser on 2026-08-27: Mark presses a button and the app updates
itself. Not automatic, not silent, not on a timer. He is told and he chooses.

The whole of it, in order:

1. The app reads `latest.json` from the bucket when it starts, in the
   background. Nothing is shown unless a newer version is announced.
2. He clicks. The app says which version and how big, and asks.
3. The zip is downloaded into a scratch folder in his home area.
4. It is checked against the `.sha256` published beside it.
5. It is unpacked and checked against its own MANIFEST, the same check the
   launcher runs on every start.
6. Only now does anything out of the bucket execute: a separate process, the
   new package's own Python running the new package's `update_apply.py`.
7. The app closes itself.

**Why step 6 is a separate process.** Windows will not let a running program
replace its own files, so the installer cannot be the app. It has to be
something that outlives it. It runs the new package's Python rather than the
old one's so that nothing in the old version folder is held open, which is what
leaves `install_windows.py` free to copy over it and to prune it.

**What the checking honestly does, and does not do.** It catches a damaged or
incomplete download: an interrupted transfer, a truncated file, a corrupted
one, a package that did not unzip whole. That is what it is for and it does it
well. Without code signing it does not prove who built the package, and it does
not protect against somebody able to rewrite both the zip in the bucket and the
`.sha256` beside it. Anyone who can replace one can replace the other. This is
an integrity check against accident, not a security control against an
adversary. It is the same limit `packaging.py` already states about the
manifest, said again here because this is the module that fetches from the
internet.

**Nothing here ever raises at a caller.** A bucket that is unreachable, empty,
slow, or serving nonsense all mean the same thing: nothing is known, nothing is
shown, and the app carries on exactly as it was. Mark is remote and will not
debug anything, and the one thing he can always do is double-click his Desktop
icon. That has to still be true after every failure in this file.

Standard library only, like `packaging.py` and `startup.py` beside it.
"""
import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request

import packaging

# Cloudflare R2, bucket `rrf-app-updates`, created 2026-08-27. Public read
# through R2's development URL, on purpose: Mark's machine downloads with no
# login, and the package holds no key and no client material, so what is
# exposed is the app itself. Spenser's call, made knowingly.
#
# Cloudflare labels this URL rate limited and not for production. That warning
# is aimed at public websites. One appraiser downloading a package now and
# again is nowhere near it, and a custom domain is the upgrade if it ever
# matters.
BUCKET = "https://pub-62e06bebd88c4f8cb46a00672f5057b2.r2.dev"

# What the app reads to learn a version exists. Written by
# tools/package_windows.py, never by hand, so Spenser uploads three files the
# script produced and types neither a version number nor a hash.
LATEST_NAME = "latest.json"

# Bounded on purpose. A pointer file is a few hundred bytes; anything larger is
# not one, and reading an unbounded body from the internet into memory on the
# startup path is how a slow morning becomes a hung app.
MAX_LATEST_BYTES = 4096
FETCH_TIMEOUT = 10.0

# Nothing larger than this is believed to be one of our packages. Measured
# 2026-08-28: v0.5.3 is 53.3 MB. The ceiling is generous rather than tight,
# because its job is to refuse something absurd, not to police a size.
MAX_PACKAGE_BYTES = 1024 * 1024 * 1024


def bucket_url() -> str:
    """Where updates come from. RRF_UPDATE_BUCKET overrides, for tests, the
    same way RRF_KEY_FILE already does for the key."""
    return (os.environ.get("RRF_UPDATE_BUCKET") or BUCKET).rstrip("/")


def file_url(name: str) -> str:
    """The address of one file in the bucket.

    The name is quoted rather than pasted, because every package name has
    spaces and a full stop in it.
    """
    return "%s/%s" % (bucket_url(), urllib.parse.quote(name))


# ------------------------------------------------------- what is out there --
def _safe_name(name) -> str:
    """A filename from the bucket, or empty if it is anything else.

    `latest.json` is a file Spenser uploads, so its contents are ours rather
    than an attacker's. It is still checked, because the value is joined onto a
    URL and a name carrying a slash would point somewhere other than the bucket
    entirely. A field that decides where the app downloads from is worth
    reading strictly whoever wrote it.
    """
    if not isinstance(name, str):
        return ""
    name = name.strip()
    if not name or not name.lower().endswith(".zip"):
        return ""
    if name.startswith(".") or ".." in name:
        return ""
    for bad in ("/", "\\", ":", "?", "#"):
        if bad in name:
            return ""
    return name


def read_latest(raw) -> dict:
    """What `latest.json` says, validated, or {} if it says nothing usable.

    Three fields and no others. A missing field, a wrong type, an unusable
    version string, a filename that could point outside the bucket, or a size
    that is not a plausible package all mean the same thing: nothing is known.
    """
    try:
        found = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    if not isinstance(found, dict):
        return {}

    version = found.get("version")
    if not isinstance(version, str) or not packaging.version_numbers(version)[0] >= 0:
        return {}

    name = _safe_name(found.get("zip"))
    if not name:
        return {}

    size = found.get("size")
    if not isinstance(size, int) or isinstance(size, bool):
        return {}
    if size <= 0 or size > MAX_PACKAGE_BYTES:
        return {}

    return {"version": version.strip(), "zip": name, "size": size}


def fetch_text(url: str, limit: int, timeout: float = FETCH_TIMEOUT) -> str:
    """A small file from the bucket, or empty.

    Reads one byte past the limit so an oversized body is noticed rather than
    silently truncated into something that might still parse.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(limit + 1)
    except (urllib.error.URLError, OSError, ValueError):
        return ""
    if len(body) > limit:
        return ""
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return ""


def announced() -> dict:
    """What the bucket is offering, whatever version it is, or {}."""
    return read_latest(fetch_text(file_url(LATEST_NAME), MAX_LATEST_BYTES))


def showing_in_a_checkout() -> bool:
    """Whether to offer updates from a development checkout. Off unless asked.

    Spenser's testing switch, added 2026-09-01. Without it he cannot see the
    update screens at all: his Mac runs the source rather than a package, so
    `available` answers "no update" and the button never renders.

    It only makes the button appear. It changes nothing else. The download, the
    hash check, the manifest check and the refusal to run anything unchecked
    all behave exactly as they do on Mark's machine, because none of them ask
    whether this is a checkout.

    It is an environment variable and never a setting, so it cannot travel in a
    package, and it is a no-op there anyway: a package is not a checkout, so
    the branch it changes is never reached.
    """
    return os.environ.get("RRF_UPDATE_IN_CHECKOUT", "") not in ("", "0")


def available(root) -> dict:
    """An update Mark could take, or {}.

    Empty in three different situations, which the caller does not need to tell
    apart because all three mean "show him nothing": the bucket said nothing
    usable, what it offered is not newer than what is running, or this is a
    development checkout.

    The checkout gate is not tidiness. Updating means installing a Windows
    package over a Windows install, and a checkout is neither. Deciding it by
    `packaging.is_checkout` reuses the same marker the launcher already trusts
    to tell a package from a development tree.
    """
    if packaging.is_checkout(root) and not showing_in_a_checkout():
        return {}
    running = packaging.version_of(root)
    offered = announced()
    if not offered:
        return {}
    if not packaging.newer(offered["version"], running):
        return {}
    return offered


# --------------------------------------------------- what the last look saw --
# A dictionary behind a lock, in the shape of progress.py beside it, and for
# the same reason: it is worthless a second after the app closes, and writing a
# temporary fact somewhere permanent is how a stale one outlives its truth.
_lock = threading.Lock()
_known = {}
_looked = False


def remember(found: dict) -> None:
    """Record what a check found, including that it found nothing."""
    global _looked
    with _lock:
        _known.clear()
        _known.update(found or {})
        _looked = True


def known() -> dict:
    """What the last check found, or {} if it found nothing or never ran."""
    with _lock:
        return dict(_known)


def looked() -> bool:
    """Whether a check has completed at all this session.

    The screen tells "we have not looked yet" apart from "we looked and there
    is nothing", because only one of those is worth a sentence to Mark.
    """
    with _lock:
        return _looked


def forget() -> None:
    """For tests, and for a fresh look."""
    global _looked
    with _lock:
        _known.clear()
        _looked = False


def look(root) -> dict:
    """Check the bucket and remember the answer. Never raises.

    This is what the background thread on startup calls, and what `Check now`
    on Settings calls. It swallows everything, because a bucket that is down
    must not be able to take the app down with it.
    """
    try:
        found = available(root)
    except Exception:
        found = {}
    remember(found)
    return found


# ============================================================= fetching it ==
# Everything below this line touches the disk. Nothing below this line
# executes anything out of the package: that is `hand_off`, and it comes after
# both checks have passed.
import hashlib          # noqa: E402  grouped with the code that uses them
import shutil           # noqa: E402


class UpdateRefused(Exception):
    """A reason not to go on, already worded the way Mark should read it.

    Same shape as `InstallRefused` and `StartupRefused`, on purpose. Every
    refusal in this app carries its own sentence rather than a code somebody
    has to look up.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


DOWNLOAD_DIR_NAME = ".rrf-app-download"

# Measured 2026-08-28 on the real v0.5.3 package: the zip is 53.3 MB and
# unpacks to 116.8 MB.
UNPACKED_RATIO = 2.2

# Three copies exist at once during an update: the zip, the tree it unpacks
# into, and the copy install_windows.py makes in the install home. Written as
# that arithmetic rather than as a number somebody picked, so it stays true if
# a package ever changes shape.
SPACE_FACTOR = 1 + 2 * UNPACKED_RATIO

# A little over, because free space reported is not free space delivered and
# the last thing this should do is fill his disk.
SPACE_MARGIN = 1.15

# Read in chunks so progress can be reported and a cancel can be noticed.
CHUNK = 1 << 18

DOWNLOAD_TIMEOUT = 60.0

# The sidecar is one line: the hash, two spaces, the filename.
HASH_CHARS = 64
MAX_SIDECAR_BYTES = 4096


def download_dir():
    """The scratch folder, in his home area and nowhere near his work.

    RRF_DOWNLOAD_DIR overrides, for tests, the same way RRF_KEY_FILE already
    does for the key.

    Deliberately not inside the install home. `install_windows.version_folders`
    reads every directory there as a version and `_prune` deletes the oldest,
    so a scratch folder there would be sorted as a version and eventually
    deleted as one. Deliberately not inside a version folder either, where
    `packaging.verify` would count it as a file that was not in the package and
    refuse to start the app.
    """
    from pathlib import Path
    override = os.environ.get("RRF_DOWNLOAD_DIR")
    return Path(override) if override else Path.home() / DOWNLOAD_DIR_NAME


def clear_scratch() -> None:
    """Empty the scratch folder, at the start of every attempt.

    At the start rather than at the end, because the process that finishes an
    update is running out of this folder and cannot delete the ground it is
    standing on. One rule, applied in one place, rather than a tidy-up that
    only sometimes gets to run.
    """
    folder = download_dir()
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True, exist_ok=True)


def space_needed(size: int) -> int:
    """Bytes that must be free before a download of this size is worth starting."""
    return int(size * SPACE_FACTOR * SPACE_MARGIN)


def _megabytes(count) -> str:
    return "%.0f MB" % (float(count) / (1024 * 1024))


def check_space(size: int) -> None:
    """Refuse before the network is touched, not half way through it."""
    folder = download_dir()
    folder.mkdir(parents=True, exist_ok=True)
    needed = space_needed(size)
    try:
        free = shutil.disk_usage(str(folder)).free
    except OSError:
        # Nothing can be said about the disk. Refusing on that would stop an
        # update that would have worked, so this is not treated as too little
        # space. A genuinely full disk fails on the write instead, plainly.
        return
    if free < needed:
        raise UpdateRefused(
            "There is not enough room on this computer to install the update.\n"
            "It needs about %s free and there is %s.\n"
            "Nothing was downloaded and nothing has changed."
            % (_megabytes(needed), _megabytes(free)))


def fetch_to_file(url: str, target, size: int, on_progress=None,
                  cancelled=None, timeout: float = DOWNLOAD_TIMEOUT):
    """Stream the package to disk, reporting progress and honouring a cancel.

    Bounded by the announced size with a chunk of slack. A file that keeps
    arriving after it should have ended is not our package, and reading it to
    the end would be filling his disk on a stranger's say-so.
    """
    ceiling = size + CHUNK
    done = 0
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            with open(str(target), "wb") as handle:
                while True:
                    if cancelled is not None and cancelled():
                        raise UpdateRefused(
                            "The update was stopped. Nothing has changed.")
                    chunk = response.read(CHUNK)
                    if not chunk:
                        break
                    done += len(chunk)
                    if done > ceiling:
                        raise UpdateRefused(
                            "The download did not match the size it said it "
                            "would be, so it was stopped. Nothing has changed.")
                    handle.write(chunk)
                    if on_progress is not None:
                        on_progress(done)
    except UpdateRefused:
        raise
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise UpdateRefused(
            "The update could not be downloaded.\n"
            "    %s\n"
            "Check the internet connection and try again. Nothing has changed."
            % exc)
    return done


def sha256_of(path) -> str:
    h = hashlib.sha256()
    with open(str(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_sidecar(text: str) -> str:
    """The hash out of a `sha256sum` line, or empty.

    The conventional shape is the hash, two spaces, the filename. Only the
    first field is read, and only if it looks like a SHA-256.
    """
    if not isinstance(text, str):
        return ""
    head = text.strip().split()
    if not head:
        return ""
    candidate = head[0].strip().lower()
    if len(candidate) != HASH_CHARS:
        return ""
    try:
        int(candidate, 16)
    except ValueError:
        return ""
    return candidate


def verify_download(path, name: str) -> str:
    """Check the file on disk against the hash published beside it.

    An unreadable, empty, or malformed sidecar is a refusal and never a skip. A
    download whose hash cannot be checked is never treated as good, because
    "we could not check" and "it is fine" are the two answers this must never
    confuse.

    What this proves: the file arrived whole and unaltered from whatever the
    bucket served. What it does not prove: who put it there. Without code
    signing, anyone who can replace the zip can replace this sidecar beside it.
    """
    published = read_sidecar(fetch_text(file_url(name + ".sha256"),
                                        MAX_SIDECAR_BYTES))
    if not published:
        raise UpdateRefused(
            "The update could not be checked, because the file that says what "
            "it should have looked like is missing or unreadable. Nothing was "
            "installed and nothing has changed.")
    actual = sha256_of(path)
    if actual != published:
        raise UpdateRefused(
            "The update did not arrive intact and was not installed.\n"
            "What arrived is not what was published, which usually means the "
            "download was interrupted.\n"
            "Nothing has changed. Try again.")
    return actual


# ================================================== how far it has got ======
# The same shape as progress.py beside it: a dictionary behind a lock, cleared
# when the run ends, never written to disk. It is a progress light and it is
# not authoritative about anything. What is true about the update is on the
# disk; this is only what to draw on the screen while it happens.
#
# Stages, in the order Mark sees them. Each is a plain sentence rather than a
# code, because it is shown to him and not to us.
DOWNLOADING = "Downloading"
CHECKING = "Checking the download"
UNPACKING = "Unpacking"
INSTALLING = "Installing"
CLOSING = "Closing"

_run_lock = threading.Lock()
_run = {}
_cancel = threading.Event()


def _blank_run() -> dict:
    return {"running": False, "stage": "", "done": 0, "total": 0,
            "error": "", "version": ""}


def begin_run(version: str, total: int) -> None:
    """A run is starting. Replaces anything left by an earlier one."""
    _cancel.clear()
    with _run_lock:
        _run.clear()
        _run.update({"running": True, "stage": DOWNLOADING, "done": 0,
                     "total": int(total), "error": "", "version": str(version)})


def set_stage(name: str) -> None:
    with _run_lock:
        if _run.get("running"):
            _run["stage"] = str(name)


def advance(done: int) -> None:
    with _run_lock:
        if _run.get("running"):
            _run["done"] = int(done)


def fail_run(message: str) -> None:
    """The run is over and it did not work. The sentence stays on screen.

    `running` goes false so the screen stops polling, and the error stays so
    there is something to read. A failure that cleared itself would leave him
    looking at a screen that had silently gone back to normal.
    """
    with _run_lock:
        _run["running"] = False
        _run["stage"] = ""
        _run["error"] = str(message)


def end_run() -> None:
    with _run_lock:
        _run.clear()
        _run.update(_blank_run())


def run_state() -> dict:
    with _run_lock:
        found = dict(_run) if _run else _blank_run()
    found["cancelling"] = _cancel.is_set()
    return found


def running() -> bool:
    with _run_lock:
        return bool(_run.get("running"))


def request_cancel() -> None:
    """Stop at the next chunk. Not a kill: the run notices and tidies up."""
    _cancel.set()


def cancelled() -> bool:
    return _cancel.is_set()


# =============================================================== unpacking ==
import zipfile           # noqa: E402  grouped with the code that uses it

UNPACKED_DIR = "unpacked"

# A package unpacks to about two and a bit times its archive. Measured
# 2026-08-28: 53.3 MB to 116.8 MB, a ratio of 2.19. The ceiling is a generous
# multiple of that rather than a tight one, because its job is to refuse
# something absurd. An archive that claims to expand twenty times is not a
# package of ours whatever else it is.
MAX_EXPANSION = 20


def _entry_is_safe(name: str, top: str) -> bool:
    """Whether one archive entry may be written to disk.

    Mirrors `package_windows._arcname`, which refuses these same shapes when
    the archive is built. Checked again here because the archive now arrives
    over the internet, and because Python's own extractor quietly sanitises a
    dangerous name instead of refusing it. Quietly sanitising is the wrong
    answer: an entry like this means the archive is not ours, and the useful
    thing to do is stop and say which entry.
    """
    if not name or name.startswith("/") or name.startswith("\\"):
        return False
    if "\\" in name or ":" in name:
        return False
    parts = name.split("/")
    if ".." in parts:
        return False
    if parts[0] != top:
        return False
    return True


def check_archive(zip_path) -> str:
    """Look through the archive without writing anything. Returns the top folder.

    Nothing is extracted until this has passed, so a hostile or damaged archive
    never gets to put a file anywhere.
    """
    try:
        with zipfile.ZipFile(str(zip_path)) as archive:
            entries = archive.infolist()
            if not entries:
                raise UpdateRefused(
                    "The update file is empty, so it was not installed. "
                    "Nothing has changed.")
            first = entries[0].filename.split("/")[0]
            if not first:
                raise UpdateRefused(
                    "The update file is not shaped like a Roy R. Fisher "
                    "package, so it was not installed. Nothing has changed.")
            declared = 0
            for entry in entries:
                if not _entry_is_safe(entry.filename, first):
                    raise UpdateRefused(
                        "The update file contains something that does not "
                        "belong in it, so it was not installed:\n"
                        "    %s\n"
                        "Nothing has changed. Send Spenser this message."
                        % entry.filename)
                declared += entry.file_size
    except UpdateRefused:
        raise
    except (zipfile.BadZipFile, OSError, ValueError):
        raise UpdateRefused(
            "The update file could not be opened, which usually means the "
            "download was interrupted. Nothing has changed. Try again.")

    try:
        on_disk = os.path.getsize(str(zip_path))
    except OSError:
        on_disk = 0
    if on_disk and declared > on_disk * MAX_EXPANSION:
        raise UpdateRefused(
            "The update file claims to unpack to far more than it could "
            "hold, so it was not installed. Nothing has changed.")
    return first


def unpack(zip_path, expect_version: str):
    """Extract the package and check it against its own manifest.

    Returns the unpacked package folder, the one holding the launcher and
    `program/`.

    This is the second of the two checks, and the last thing that happens
    before anything out of the bucket is allowed to execute. It is the same
    `packaging.verify` the launcher runs on every start, so a package that
    would not have started is refused here rather than after it is installed.
    """
    from pathlib import Path

    top = check_archive(zip_path)
    where = download_dir() / UNPACKED_DIR
    if where.exists():
        shutil.rmtree(where, ignore_errors=True)
    where.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(str(zip_path)) as archive:
            archive.extractall(str(where))
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        shutil.rmtree(where, ignore_errors=True)
        raise UpdateRefused(
            "The update could not be unpacked:\n"
            "    %s\n"
            "Nothing has changed. Try again." % exc)

    package = Path(where) / top
    inner = packaging.program_dir(package)
    try:
        packaging.verify(inner)
    except packaging.PackageDamaged as exc:
        shutil.rmtree(where, ignore_errors=True)
        raise UpdateRefused(exc.message)

    found = packaging.version_of(inner)
    if found != str(expect_version).strip():
        shutil.rmtree(where, ignore_errors=True)
        raise UpdateRefused(
            "The update said it was version %s and turned out to be %s, so it "
            "was not installed. Nothing has changed. Send Spenser this "
            "message." % (expect_version, found or "unnamed"))
    return package


# ============================================== handing over, and leaving ===
import subprocess       # noqa: E402  grouped with the code that uses it

import startup          # noqa: E402  standard library only, like this module

# What passed both checks in this run, and nothing else may be executed.
#
# The order of this file is the safety property: download, check the hash,
# unpack, check the manifest, and only then run something. An order that
# depends on every caller remembering it is not a safety property, so the
# record below is written inside `prepare` and cannot be set from outside.
# `hand_off` refuses anything that is not in it.
_cleared_lock = threading.Lock()
_cleared = {"package": "", "sha256": ""}


def _mark_cleared(package, digest: str) -> None:
    with _cleared_lock:
        _cleared["package"] = str(package)
        _cleared["sha256"] = str(digest)


def _is_cleared(package) -> bool:
    with _cleared_lock:
        return bool(_cleared["sha256"]) and _cleared["package"] == str(package)


def forget_cleared() -> None:
    with _cleared_lock:
        _cleared["package"] = ""
        _cleared["sha256"] = ""


def prepare(offer: dict, on_progress=None):
    """Download it, check it, unpack it, check it again. Returns the package.

    Nothing out of the bucket has executed when this returns. That is the whole
    point of it being one function: the four steps happen in one place, in one
    order, and the thing that follows them refuses to run anything this did not
    clear.
    """
    from pathlib import Path

    forget_cleared()
    clear_scratch()
    check_space(int(offer["size"]))

    target = Path(download_dir()) / offer["zip"]
    set_stage(DOWNLOADING)
    fetch_to_file(file_url(offer["zip"]), target, int(offer["size"]),
                  on_progress=on_progress, cancelled=cancelled)

    set_stage(CHECKING)
    digest = verify_download(target, offer["zip"])

    set_stage(UNPACKING)
    package = unpack(target, offer["version"])

    _mark_cleared(package, digest)
    return package


def handoff_command(package):
    """The command that finishes the update, or a refusal.

    The new package's own Python running the new package's own
    `update_apply.py`. Never the running version's copy of either: once this
    starts, nothing in the old version folder may be held open, because that is
    what leaves `install_windows.py` free to copy over it and to prune it.
    """
    from pathlib import Path

    inner = Path(packaging.program_dir(package))
    python = inner / "python" / "python.exe"
    script = inner / "app" / "update_apply.py"
    if not script.is_file():
        raise UpdateRefused(
            "The update does not carry the part that installs it, so it was "
            "not installed. Nothing has changed. Send Spenser this message.")
    if not python.is_file():
        raise UpdateRefused(
            "The update does not carry the Python it needs, so it was not "
            "installed. Nothing has changed. Send Spenser this message.")
    return [str(python), str(script)]


def hand_off(package, spawn=None) -> list:
    """Start the process that will finish the update, and return its command.

    Refuses anything that did not pass both checks in this run. This is the
    first line in the whole update that executes something out of the bucket,
    and it is guarded by a record no caller can write.
    """
    if not _is_cleared(package):
        raise UpdateRefused(
            "The update was not checked, so it was not installed. Nothing has "
            "changed. Send Spenser this message.")

    command = handoff_command(package)
    if spawn is None:
        spawn = subprocess.Popen

    options = {"cwd": str(packaging.program_dir(package)), "close_fds": True}
    # Its own console window on Windows. That window is the only place a plain
    # failure message can land once this app has closed, and the pilot decision
    # to keep the console visible applies to it at least as much as to the
    # launcher.
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    if flags:
        options["creationflags"] = flags

    try:
        spawn(command, **options)
    except (OSError, subprocess.SubprocessError) as exc:
        raise UpdateRefused(
            "The update was downloaded and checked but could not be started:\n"
            "    %s\n"
            "Nothing has changed and this app is still running." % exc)
    return command


def close_the_app(home, exit_now=None) -> None:
    """Clear this copy's runtime record and go.

    The record describes a running app, so leaving it behind names a process
    that is not there. The installer waiting on the other side asks the port it
    names whether our version answers, and a dead port answers nothing, so a
    missed tidy-up is already safe. Doing it properly costs one line.

    Exits rather than shutting uvicorn down politely, because the whole purpose
    of this call is to stop holding files open. `exit_now` is injected so a
    test can watch it happen without dying.
    """
    set_stage(CLOSING)
    try:
        startup.clear_runtime(home)
    except Exception:
        pass
    if exit_now is None:
        def exit_now():
            os._exit(0)
    exit_now()

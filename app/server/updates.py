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
    if packaging.is_checkout(root):
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

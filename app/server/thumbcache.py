"""Where the screen's thumbnails are kept, which is not in Mark's job folder.

The app used to write a hidden `.rrf-thumbs` folder inside the job's own
Photos folder, beside his photographs, and fill it with names like
`photo-01.jpg.jpg`. Two things wrong with that, and the second is the one that
matters.

The doubled extension was a bug: the cached name was the source name with
`.jpg` appended rather than substituted.

Writing there at all breaks the rule the whole app is built on. A job folder is
Mark's, and his client's. Everything the app knows about a job is the app's own
note and lives outside his folders, so that nothing the app records ever
appears in something he delivers. A cache is exactly such a note.

Identity is the resolved path of the job's Photos folder, hashed. Two jobs with
the same folder name in two different workspaces are different jobs and must
not share a thumbnail; hashing the full resolved path is what keeps them apart
without putting a readable client path in a filename.

Nothing here deletes an old `.rrf-thumbs`. Removing a folder from inside one of
his jobs is a bigger decision than fixing where new files go, and it is not
this module's to make.
"""
import hashlib
import os
import re
import time
from pathlib import Path

CACHE_NAME = ".rrf-app-cache"

# The old location, kept only so the rest of the app can carry on ignoring it
# when it lists a Photos folder. Nothing writes here any more, and nothing here
# ever deletes one: it sits inside one of Mark's own job folders, and removing
# anything from those is a separate decision that has not been made.
LEGACY_THUMB_DIR = ".rrf-thumbs"

# What this module is allowed to delete, and nothing else. A folder directly
# inside the cache whose name is one of our own fingerprints, holding files
# whose names are one of our own thumbnails. Anything that does not match both
# shapes is left alone, so a cache path pointed somewhere unexpected can only
# ever be a no-op rather than a disaster.
OWNED_FOLDER = re.compile(r"^[0-9a-f]{16}$")
OWNED_FILE = re.compile(r"^.+-[0-9a-f]{8}\.jpg$")

# A thumbnail is a convenience: it costs one image resize to rebuild and the
# app is unusable to nobody while that happens. Anything untouched for this
# long is cheaper to make again than to keep.
KEEP_DAYS = 30

# How much work one prune may do. Startup must never wait on a folder that has
# grown for years, so the sweep stops at this many folders and picks up the
# rest next time rather than trying to finish in one go.
MAX_FOLDERS_PER_SWEEP = 200


def cache_root() -> Path:
    """Home folder on both Mac and Windows. RRF_CACHE_DIR overrides, for
    tests, the same way RRF_KEY_FILE already does for the key."""
    override = os.environ.get("RRF_CACHE_DIR")
    return Path(override) if override else Path.home() / CACHE_NAME


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()[:16]


def folder_for(photos_dir: Path) -> Path:
    """This job's own corner of the cache, by resolved path.

    Resolved rather than as given, so the same folder reached two ways is one
    cache entry. A folder that cannot be resolved is still answered for, using
    the path as written: a thumbnail is a convenience and a cache miss is a
    tolerable outcome, but raising here would take the screen down.
    """
    try:
        key = str(Path(photos_dir).resolve())
    except OSError:
        key = str(photos_dir)
    return cache_root() / _fingerprint(key)


def cached_file(photos_dir: Path, name: str) -> Path:
    """The cached thumbnail for one photograph.

    `.jpg` replaces the source extension rather than being appended to it, so a
    thumbnail of `photo-01.jpg` is `photo-01-<hash>.jpg` and never
    `photo-01.jpg.jpg`. The hash of the full original name is what keeps
    `roof.jpg` and `roof.png` apart, which substituting the extension alone
    would silently merge into one.
    """
    bare = Path(name).name
    return folder_for(photos_dir) / ("%s-%s.jpg" % (Path(bare).stem, _fingerprint(bare)[:8]))


def is_stale(cached: Path, source: Path) -> bool:
    """Whether the cached copy is missing or older than the photograph.

    A source that cannot be read is treated as stale, so the caller goes and
    opens it and reports the real error, rather than serving a thumbnail of a
    photograph that may no longer be there.
    """
    try:
        if not cached.exists():
            return True
        return cached.stat().st_mtime < source.stat().st_mtime
    except OSError:
        return True


def prune(keep_days: int = KEEP_DAYS, budget: int = MAX_FOLDERS_PER_SWEEP,
          now: float = None) -> dict:
    """Delete cache folders nothing has used lately. Bounded, and app-owned only.

    Three limits, and each one is deliberate.

    It only ever looks inside the cache root, and only at folders and files
    whose names match the shapes this module writes. A folder someone else put
    there, or a cache root pointed at the wrong place, is skipped rather than
    emptied.

    It stops after `budget` folders. This runs at startup, and a sweep that
    tried to finish on a cache grown over years would make the app feel broken
    on exactly the machines where it had most to do. What it does not reach, it
    reaches next time.

    It never raises. Tidying is worth doing and never worth failing over, so a
    permission error on one folder skips that folder and the app carries on.

    Legacy `.rrf-thumbs` folders are not touched, and cannot be: they live
    inside Mark's job folders, and nothing here looks outside the cache root.
    """
    now = time.time() if now is None else now
    cutoff = now - (max(0, keep_days) * 86400)
    report = {"looked_at": 0, "removed": 0, "kept": 0, "freed_bytes": 0,
              "stopped_early": False}

    root = cache_root()
    try:
        if not root.is_dir():
            return report
        entries = sorted(os.scandir(root), key=lambda e: e.name)
    except OSError:
        return report

    for entry in entries:
        if report["looked_at"] >= budget:
            report["stopped_early"] = True
            break
        try:
            # follow_symlinks=False: a link planted here must never be walked
            # into, and must never be followed on the way to unlink().
            if not entry.is_dir(follow_symlinks=False):
                continue
            if not OWNED_FOLDER.match(entry.name):
                continue
            report["looked_at"] += 1
            folder = Path(entry.path)
            files = [f for f in os.scandir(folder)
                     if f.is_file(follow_symlinks=False) and OWNED_FILE.match(f.name)]
            strays = [f for f in os.scandir(folder) if not OWNED_FILE.match(f.name)]
            newest = max((f.stat().st_mtime for f in files), default=0.0)
            if strays or newest >= cutoff:
                # Something in here is not ours, or something in here is still
                # in use. Either way it stays.
                report["kept"] += 1
                continue
            freed = sum(f.stat().st_size for f in files)
            for f in files:
                os.unlink(f.path)
            folder.rmdir()          # refuses if anything unexpected is left
            report["removed"] += 1
            report["freed_bytes"] += freed
        except OSError:
            continue

    return report

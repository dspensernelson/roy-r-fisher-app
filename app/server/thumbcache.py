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
from pathlib import Path

CACHE_NAME = ".rrf-app-cache"

# The old location, kept only so the rest of the app can carry on ignoring it
# when it lists a Photos folder. Nothing writes here any more.
LEGACY_THUMB_DIR = ".rrf-thumbs"


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

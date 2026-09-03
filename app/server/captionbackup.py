"""One spare copy of a job's photo manifest, kept outside the job folder.

`photo-manifest.json` holds every caption typed on a job, and it used to be
written with a plain `path.write_text`: no temporary file, no previous copy.
A write that failed partway left a truncated file and nothing to recover from.

`state.write_text` already fixes the failure-partway case: the real file is
never touched until the new one is complete. This module fixes the other one,
which `state.write_text` cannot: it keeps the version from *before* the write
that is about to happen, so a save that succeeds but is simply wrong can still
be undone by hand.

One spare per job, overwritten on every save. Not a history, because a history
needs pruning and this does not: it is bounded by the number of jobs Spenser
has open, which is small.

Kept beside the thumbnail cache, fingerprinted the same way, so a job's spare
and its thumbnails share one identity and one place to look. The folder name
`captions` never matches `thumbcache.OWNED_FOLDER`, so `thumbcache.prune` never
touches it and is never confused by it either.
"""
from pathlib import Path

import state
import thumbcache


def spare_for(photos_dir: Path) -> Path:
    """Where this job's spare manifest lives, keyed the same way a thumbnail
    is: the resolved path of the job's Photos folder, hashed."""
    try:
        key = str(Path(photos_dir).resolve())
    except OSError:
        key = str(photos_dir)
    fingerprint = thumbcache._fingerprint(key)
    return thumbcache.cache_root() / "captions" / ("%s.json" % fingerprint)


def keep(photos_dir: Path, current_text: str) -> None:
    """Save `current_text` as this job's spare, replacing whatever was there.

    Called with the manifest's contents from just before a save overwrites it,
    so the spare always holds the version before the most recent write.

    Never raises. A spare that could not be written is a worse day, not a
    failed save: the save this protects must still happen.
    """
    try:
        state.write_text(spare_for(photos_dir), current_text)
    except (OSError, state.StateUnreadable):
        pass

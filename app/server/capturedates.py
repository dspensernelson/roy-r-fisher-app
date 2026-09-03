"""What each photograph is, remembered, so it is opened once and not again.

`exif_order` opens every photograph it is handed to read the capture time out
of it, and `load_manifest` hands it every file the list does not already know.
The answer is then thrown away, because `load_manifest` never writes back: a
plain read must not have a side effect, and that rule stays.

So the same files were opened again on the next click, and the next, for ever.
Measured 2026-09-02 on the Blaul Lofts job: one tick of `Mark Reviewed` cost
130 file opens. Measured again on 2026-09-03 from Colleen's machine in Mark's
office, where the job sits on a network drive and every open is a question
asked of another computer:

    GET .../caption-estimate  ms=11374
    GET .../caption-estimate  ms=10031
    GET .../caption-estimate  ms=9415

**The dates live beside the photograph list and never inside it.** That is the
whole design. Writing them into `photo-manifest.json` would mean this change
opens the file holding every caption in the job for writing, and that file is
the one thing nobody can afford to lose. Kept apart, this change cannot cost
anybody a caption, however wrong it turns out to be.

Same home as the thumbnails, fingerprinted the same way, so one job has one
identity and one place to look. The folder is called `dates`, which never
matches `thumbcache.OWNED_FOLDER`, so `thumbcache.prune` steps over it rather
than treating it as a stray and pinning the thumbnails beside it forever.

Staleness is the file's own modification time, which is the rule
`thumbcache.is_stale` already uses. One rule in the app, not two.

Two things are remembered per photograph, because two different pieces of
the app were opening the same files over and over for two different
reasons. `stamp` is the capture time, read by `exif_order` to put new
photographs in order. `size` is how many bytes the photograph becomes once
it is shrunk and encoded for the model, which `captions.plan_tranches`
needs to decide how many fit in one request.

**The second one was the worse of the two and nobody had noticed.** Working
out that size means decoding the photograph, resizing it to 1024, encoding
it again as JPEG and base64ing the result. `caption-estimate` did that for
every uncaptioned photograph, and the screen asks for a fresh estimate
after every single click. Measured from Colleen's own machine on
2026-09-03, on a job of 40 photographs on a network drive, that is what
`caption-estimate  ms=11374` was.
"""
import json
from pathlib import Path

import state
import thumbcache


def store_for(photos_dir: Path) -> Path:
    """Where this job's remembered dates live, keyed the way a thumbnail is:
    the resolved path of the job's Photos folder, hashed."""
    try:
        key = str(Path(photos_dir).resolve())
    except OSError:
        key = str(photos_dir)
    return thumbcache.cache_root() / "dates" / ("%s.json" % thumbcache._fingerprint(key))


def _read(store: Path) -> dict:
    """What we remember, or nothing. Never raises: a cache that cannot be read
    is a slow day, not a broken one."""
    try:
        if store.is_file():
            found = json.loads(store.read_text(encoding="utf-8"))
            if isinstance(found, dict):
                return found
    except Exception:
        pass
    return {}


def _write(store: Path, known: dict) -> None:
    """Never raises, for the same reason. Through `state.write_text`, so a
    half-written cache cannot exist even if the machine stops mid-save."""
    try:
        state.write_text(store, json.dumps(known, indent=2))
    except Exception:
        pass


def _stamp_from_disk(path: Path) -> str:
    """The capture time out of the file itself, or empty.

    Empty covers every failure the same way `exif_order` always has: a
    photograph with no capture time, one this machine cannot decode, one that
    is not really an image. All of them fall back to sorting by name.
    """
    from photo_pages import Image, _DATETIME_TAG
    try:
        exif = Image.open(path).getexif()
        stamp = exif.get(_DATETIME_TAG) or exif.get(306)   # 306 = DateTime
        return str(stamp) if stamp else ""
    except Exception:
        return ""


def _entry(known: dict, name: str, mtime: float) -> dict:
    """This photograph's record, fresh if the file has changed under it."""
    found = known.get(name)
    if isinstance(found, dict) and found.get("mtime") == mtime:
        return found
    made = {"mtime": mtime}
    known[name] = made
    return made


def size_for(job: Path):
    """A reader that answers how large a photograph becomes once it is
    prepared for the model, opening each one at most once.

    Same shape and same store as `stamp_for`. Kept as a separate function
    rather than folded into that one because the two callers are far apart:
    the ordering pass wants capture times, and the price estimate wants sizes,
    and neither should have to know about the other's needs.
    """
    photos_dir = job / "Photos"
    store = store_for(photos_dir)
    known = _read(store)
    dirty = []

    def reader(path) -> int:
        from captions import _encoded_size
        path = Path(path)
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return _encoded_size(path)

        record = _entry(known, path.name, mtime)
        if "size" in record:
            return int(record["size"])

        size = _encoded_size(path)
        record["size"] = size
        if not dirty:
            dirty.append(True)
        return size

    def flush() -> None:
        if dirty:
            _write(store, known)

    reader.flush = flush
    return reader


def stamp_for(job: Path):
    """A reader for one job that opens each photograph at most once.

    Returns a function, rather than doing the work here, so a whole ordering
    pass shares one read of the store and one write at the end instead of one
    of each per photograph. On a network drive that difference is the point.

    The returned function answers from memory when the file has not changed
    since it was last looked at, and reads the file when it has. A file whose
    modification time cannot be read is treated as changed, which is slower and
    never wrong.
    """
    photos_dir = job / "Photos"
    store = store_for(photos_dir)
    known = _read(store)
    dirty = []

    def reader(path: Path) -> str:
        name = str(Path(path).name)
        try:
            mtime = Path(path).stat().st_mtime
        except OSError:
            return _stamp_from_disk(path)

        record = _entry(known, name, mtime)
        if "stamp" in record:
            return str(record["stamp"])

        stamp = _stamp_from_disk(path)
        record["stamp"] = stamp
        if not dirty:
            dirty.append(True)
        return stamp

    def flush() -> None:
        if dirty:
            _write(store, known)

    reader.flush = flush
    return reader

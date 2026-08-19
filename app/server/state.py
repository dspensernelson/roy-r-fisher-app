"""One way to write the app's own files, so a crash can never lose Mark's setup.

Every file the app owns lives in his home folder, outside the package and
outside his job folders. Three of them existed before this module and they did
not behave the same way: `classify.py` wrote through a temporary file and
replaced it, while `workspace.py` and `settings.py` wrote straight over the
real file. A power cut or a force quit during one of those direct writes leaves
a half-written file, and the code that read it treated the damage as "he has
not set anything up yet". That is the same screen he sees on a brand new
machine, so the app would quietly ask him to choose his jobs folder again and
never say why.

Two ideas carry this module.

Writing is always temporary-file-then-replace, in the destination's own
directory so the replace is a rename inside one filesystem and therefore
atomic. If anything fails, the previous file is still exactly as it was, and
the only thing cleaned up is this module's own temporary file.

Reading never invents. A file that is not there means no settings, which is a
real and ordinary state. A file that is there but cannot be read is a different
state entirely, and it raises rather than returning nothing, because returning
nothing is indistinguishable from a fresh install. The damaged file is never
repaired, renamed, or deleted: it is left byte for byte as it is, so it can be
recovered.
"""
import json
import os
from pathlib import Path

# What the app owns and may rewrite. Nothing else in the home folder is ours.
SCHEMA_KEY = "schema"
CURRENT_SCHEMA = 1

# A file written before this module existed carries no schema key. It is not
# damaged and it is not old enough to refuse: it is simply version 0, and it
# reads exactly as it always did.
LEGACY_SCHEMA = 0

# One sentence, approved 2026-08-19. Mark never sees a traceback or raw JSON
# error text. He sees this, and it tells him the two things that matter: that
# nothing was destroyed, and who to ask.
RECOVERABLE_MESSAGE = ("The app's saved settings could not be read. "
                       "The file was not changed. Contact Spenser before continuing.")


class StateUnreadable(Exception):
    """A file the app owns is there but cannot be trusted.

    Carries the plain sentence for the screen and a separate technical reason
    that stays in tests and diagnostics. The two are deliberately different:
    the reason names the file and the fault, and it is never what Mark reads.
    """

    def __init__(self, path, reason: str):
        super().__init__(reason)
        self.path = str(path)
        self.reason = reason
        self.message = RECOVERABLE_MESSAGE


class StateTooNew(StateUnreadable):
    """Written by a newer version of the app than this one.

    A separate class because it is a separate situation: nothing is damaged,
    this copy simply does not know the shape. Refusing is the only safe answer,
    because guessing at a shape we do not know is how a newer version's
    settings get silently truncated by an older one after a rollback.
    """


def _guard(path: Path) -> Path:
    """Refuse to write through anything that leaves the folder we were given.

    `Path.write_text` on a symlink writes to whatever the link points at. A
    link left where one of our files belongs would let a write land anywhere on
    disk, including inside one of Mark's job folders, which the Never list
    forbids. Resolving the parent and comparing is what catches it, and the
    symlink check catches the case where the file itself is the link.
    """
    path = Path(path)
    if path.is_symlink():
        raise StateUnreadable(path, "app-owned state path is a link")
    parent = path.parent
    if parent.exists() and parent.resolve() != parent.absolute().resolve():
        raise StateUnreadable(path, "app-owned state folder is a link")
    return path


def secure(path: Path) -> None:
    """Owner-only, where the operating system has such a thing.

    Windows has no POSIX mode bits and raises for them. The file still sits in
    the user's own profile folder, which is the protection that matters there,
    so failing here would be refusing to work on the machine this app is for.
    """
    try:
        Path(path).chmod(0o600)
    except (OSError, NotImplementedError, AttributeError):
        pass


def write_text(path, text: str, owner_only: bool = False) -> None:
    """Replace this file's contents, or leave the previous file untouched.

    The temporary file is created in the destination's own directory on
    purpose. A temporary file in the system temp folder would sit on a
    different filesystem, and the replace would become a copy, which is not
    atomic and is exactly the half-written file this module exists to prevent.
    """
    path = _guard(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # The pid keeps two writers from choosing the same temporary name. The
    # suffix stays ".writing" so the existing tests that sweep for leftovers
    # still find ours.
    temp = path.with_name("%s.%d.writing" % (path.name, os.getpid()))
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except (OSError, AttributeError):
                # Some filesystems and some platforms do not offer it. The
                # replace below is still atomic; only the durability guarantee
                # across a power cut is weaker, and that is not worth refusing
                # to save over.
                pass
        if owner_only:
            secure(temp)
        os.replace(str(temp), str(path))
    except Exception:
        # Only ever our own temporary file. The real file is never touched on
        # this path, which is the whole point.
        try:
            if temp.exists():
                temp.unlink()
        except OSError:
            pass
        raise


def write_json(path, data: dict, owner_only: bool = False) -> None:
    """Write a structured app-owned file, stamped with the current schema.

    Stamping happens here rather than in each caller so no file can be written
    without a version. `ensure_ascii=False` keeps an accented folder name
    readable in the file instead of escaped, and the encoding is stated rather
    than left to the machine, because Windows would otherwise pick a codepage
    that mangles it.
    """
    body = dict(data)
    body[SCHEMA_KEY] = CURRENT_SCHEMA
    write_text(path, json.dumps(body, ensure_ascii=False, indent=2) + "\n",
               owner_only=owner_only)


def read_json(path) -> dict:
    """What is in this file, or {} when there is no file.

    Raises StateUnreadable when the file is there and cannot be trusted.
    Never repairs, renames, or deletes it.

    The difference between "absent" and "damaged" is the entire reason this
    function exists. Absent is ordinary: he has not chosen a jobs folder yet.
    Damaged is not ordinary, and answering it with {} would show him the
    first-run screen and let him believe the app forgot him.
    """
    path = Path(path)
    if path.is_symlink():
        raise StateUnreadable(path, "app-owned state path is a link")
    if not path.is_file():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise StateUnreadable(path, "cannot read: %s" % type(exc).__name__)
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise StateUnreadable(path, "not valid JSON: %s" % exc)
    if not isinstance(data, dict):
        raise StateUnreadable(path, "expected an object, found %s"
                              % type(data).__name__)

    found = data.get(SCHEMA_KEY, LEGACY_SCHEMA)
    if not isinstance(found, int) or isinstance(found, bool):
        raise StateUnreadable(path, "schema is not a whole number")
    if found > CURRENT_SCHEMA:
        raise StateTooNew(path, "written by a newer version (schema %d)" % found)
    if found < LEGACY_SCHEMA:
        raise StateUnreadable(path, "schema is negative")
    return data


def schema_of(data: dict) -> int:
    """Which shape this data was read as. 0 means it predates versioning.

    Reading a legacy file never rewrites it. It is only stamped when the next
    real save happens, so merely opening the app cannot change a file on disk.
    """
    found = data.get(SCHEMA_KEY, LEGACY_SCHEMA)
    return found if isinstance(found, int) and not isinstance(found, bool) else LEGACY_SCHEMA


def without_schema(data: dict) -> dict:
    """The payload without the bookkeeping key, for callers that iterate it."""
    return {k: v for k, v in data.items() if k != SCHEMA_KEY}

"""The package's own inventory, and the check that it arrived whole.

Mark unzips one folder and double-clicks once. Windows Explorer's built-in
extraction is slow on a package carrying an embedded interpreter, and a cancel
part way through leaves a folder that still has a launcher in it. That is the
dangerous shape: it starts, and then fails somewhere less obvious, with a
Python traceback as the only thing on screen.

So the launcher checks the package before it imports anything that could
produce such a traceback. Everything here is standard library only, on purpose:
it has to be able to run and to speak plainly in a package whose third-party
wheels are exactly what went missing.

Two files are deliberately outside the immutable set.

`runtime.json` is written at startup and holds the port that was bound, so it
changes every run. Including it would mean the app invalidated its own package
the first time it started.

`MANIFEST` cannot contain a hash of itself, so it is excluded from its own
aggregate. Nothing else is.

What this proves and what it does not. It detects a damaged or incomplete
package: an interrupted extraction, a truncated download, a corrupted file, a
file that moved. It does not prove who built the package. Without code signing
anyone able to rewrite the files can rewrite the manifest beside them, so this
is an integrity check against accident, not a security control against an
adversary. That is a known and accepted limit for this pilot.
"""
import hashlib
import os
from pathlib import Path

MANIFEST_NAME = "MANIFEST"
VERSION_NAME = "VERSION"
RUNTIME_NAME = "runtime.json"

# The practice job that ships in the package. It is Mark's to work in: opening
# it writes a photo manifest, captions land in it, and built documents are
# saved into its Photos folder. So it is shipped content but it is not
# immutable content, and listing it would mean the app refused to start the
# moment he used the demo it came with.
DEMO_DIR = "Demo Jobs"

# Never listed, never hashed. See the module docstring for why each one.
OUTSIDE_THE_SET = (MANIFEST_NAME, RUNTIME_NAME)

# Never packaged even when they appear in a source tree. The exclusion list in
# the plan is the requirement; these are the ones a directory walk would
# otherwise sweep up on its own.
NOISE_DIRS = {"__pycache__", ".pytest_cache", ".git", "node_modules", ".rrf-thumbs"}
NOISE_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}


class PackageDamaged(Exception):
    """The package on disk is not the package that was built.

    Carries a plain sentence naming what is wrong and which file, because the
    whole point is that Mark reads it instead of a traceback.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def is_checkout(root: Path) -> bool:
    """True when this is the development tree rather than a built package.

    A checkout has no MANIFEST and never will: the manifest is generated at
    packaging time. So the launcher has to tell the two apart, and it has to do
    it by something a package can never contain, not by the absence of the
    manifest itself. Otherwise "the manifest is missing" and "there was never
    meant to be one" would look identical, and an unzip that dropped the
    manifest would skip the check silently, which is the one case it exists
    for.

    `app/tests` is that marker. It is on the exclusion list, the packaging
    script never copies it, and a packaging test asserts it is absent from the
    built package. So its presence means development, and its absence means
    this is meant to be a package and the manifest is required.
    """
    return (Path(root) / "app" / "tests").is_dir()


def package_root(start=None) -> Path:
    """The folder holding VERSION, the launcher, and app/.

    `run_app.py` lives at `<root>/app/run_app.py` in the built package and at
    `<repo>/app/run_app.py` in the checkout, so the same two-steps-up answer is
    right in both places and no branch is needed.
    """
    here = Path(start) if start else Path(__file__).resolve()
    return here.parents[2] if start is None else Path(start)


def version_of(root: Path) -> str:
    """The version string in the package's VERSION file, or empty.

    Read rather than compiled in, because packaging writes it and rollback
    tells two folders apart by it. A constant in the source could not be
    inspected without running the app, which is the moment it is least
    available.
    """
    path = Path(root) / VERSION_NAME
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return ""


def _walk(root: Path):
    """Every immutable file under root, as relative posix paths, sorted.

    Sorted so two machines building from the same inputs produce the same
    manifest and the same aggregate. Unsorted would make the aggregate depend
    on the order the filesystem happened to hand things back.
    """
    root = Path(root)
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in NOISE_DIRS)
        if Path(dirpath) == root:
            # Working data, not package content. Everything else under the
            # root is code or runtime and never changes after it is unzipped.
            dirnames[:] = [d for d in dirnames if d != DEMO_DIR]
        for name in sorted(filenames):
            if name in NOISE_FILES:
                continue
            full = Path(dirpath) / name
            rel = full.relative_to(root).as_posix()
            if rel in OUTSIDE_THE_SET:
                continue
            found.append(rel)
    return sorted(found)


def aggregate(root: Path, entries=None) -> str:
    """One SHA-256 over the ordered paths, sizes, and contents of the set.

    Paths and sizes as well as contents on purpose. Contents alone would not
    notice a file moved to a different place in the package, and size is the
    cheap half that catches a truncated extraction without reading every byte
    twice.
    """
    root = Path(root)
    rows = _walk(root) if entries is None else sorted(entries)
    h = hashlib.sha256()
    for rel in rows:
        full = root / rel
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(str(full.stat().st_size).encode("ascii"))
        h.update(b"\0")
        with open(full, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                h.update(chunk)
        h.update(b"\n")
    return h.hexdigest()


def build_manifest(root: Path) -> str:
    """The manifest text for a freshly built package.

    Plain text rather than JSON so a person can read it over a screen share
    without a tool.
    """
    root = Path(root)
    entries = _walk(root)
    lines = ["# Roy R. Fisher package manifest",
             "# Every immutable file, its size in bytes, and one aggregate over",
             "# the ordered paths, sizes and contents of all of them.",
             "version %s" % (version_of(root) or "unknown"),
             "aggregate sha256:%s" % aggregate(root, entries),
             "files %d" % len(entries)]
    for rel in entries:
        lines.append("%d %s" % ((root / rel).stat().st_size, rel))
    return "\n".join(lines) + "\n"


def read_manifest(root: Path) -> dict:
    """Parse the manifest beside the package, or say it is not there."""
    path = Path(root) / MANIFEST_NAME
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        raise PackageDamaged(
            "This copy is missing its %s file, so the app cannot check that it "
            "unzipped completely. Unzip the package again." % MANIFEST_NAME)

    found = {"version": "", "aggregate": "", "files": {}}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        head, _, rest = line.partition(" ")
        if head == "version":
            found["version"] = rest.strip()
        elif head == "aggregate":
            found["aggregate"] = rest.strip()
        elif head == "files":
            continue
        elif head.isdigit():
            found["files"][rest.strip()] = int(head)
        else:
            raise PackageDamaged(
                "The %s file in this copy is not readable, so the app cannot "
                "check that it unzipped completely. Unzip the package again."
                % MANIFEST_NAME)
    if not found["aggregate"]:
        raise PackageDamaged(
            "The %s file in this copy has no checksum in it. Unzip the package "
            "again." % MANIFEST_NAME)
    return found


def verify(root: Path) -> None:
    """Raise PackageDamaged unless this folder is exactly what was built.

    Ordered cheapest and most specific first. Naming the one missing file is
    far more use over a screen share than a checksum mismatch, so the per-file
    checks run before the aggregate even though the aggregate would catch them
    too.
    """
    root = Path(root)
    listed = read_manifest(root)

    for rel, size in sorted(listed["files"].items()):
        full = root / rel
        if not full.is_file():
            raise PackageDamaged(
                "This copy is missing a file it needs: %s. The unzip did not "
                "finish. Delete this folder and unzip the package again." % rel)
        actual = full.stat().st_size
        if actual != size:
            raise PackageDamaged(
                "A file in this copy is the wrong size: %s. The unzip did not "
                "finish. Delete this folder and unzip the package again." % rel)

    present = set(_walk(root))
    extra = sorted(present - set(listed["files"]))
    if extra:
        raise PackageDamaged(
            "This copy has a file that was not in the package: %s. Delete this "
            "folder and unzip the package again." % extra[0])

    expected = listed["aggregate"].split(":")[-1]
    if aggregate(root, listed["files"]) != expected:
        raise PackageDamaged(
            "The files in this copy do not match the package they came from. "
            "Something changed them or the download was incomplete. Delete "
            "this folder and unzip the package again.")

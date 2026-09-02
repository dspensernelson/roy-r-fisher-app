"""Reset the demo jobs folder to a known baseline, for testing only.

This is Spenser's tool for running the same experience from the beginning,
over and over, while we build it. It is never Mark's. Without a valid
`.rrf-demo.json` the button does not render and the endpoint answers 404,
and the whole thing is removed from anything delivered to him.

Two ideas carry the safety.

It makes no deletion decisions. It does not hunt for generated captions,
built documents, thumbnails or files added mid-test. It replaces the whole
working folder with the baseline, so all of that is gone because it simply
is not in the baseline, and no filename is ever guessed at.

And it will only ever touch four exact locations. Being somewhere inside the
repo is not enough: each configured path must resolve to precisely the
approved place, with no symlink in the way. Configuring `app/` as the
working folder fails, and fails without touching it.
"""
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Optional

import workspace

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / ".rrf-demo.json"
CHECKSUM_NAME = "BASELINE.sha256"

# The only four places this code may ever touch, as repo-relative literals.
# The configuration names its paths and they must equal these exactly.
APPROVED = {
    "baseline": ".rrf-demo-baseline/RRF Demo Jobs",
    "working": "TEST JOBS",
    "staging": ".rrf-demo-staging",
    "rollback": ".rrf-demo-rollback/RRF Demo Jobs",
}


class DemoError(Exception):
    """Something did not check out. Carries a report for the caller."""

    def __init__(self, message: str, report: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.report = report or {}


# ------------------------------------------------------------ fingerprints --
def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(root: Path) -> dict:
    """Every file under root, by relative path, with its own checksum."""
    out = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            full = Path(dirpath) / name
            out[full.relative_to(root).as_posix()] = sha256_of(full)
    return out


def aggregate(prints: dict) -> str:
    """One number standing for a whole tree, so a report can quote it.

    SHA-256 over each relative path and its own checksum, in sorted path
    order, separated so no two different trees can collide by concatenation.
    """
    h = hashlib.sha256()
    for rel in sorted(prints):
        h.update(rel.encode("utf-8")); h.update(b"\0")
        h.update(prints[rel].encode()); h.update(b"\n")
    return h.hexdigest()


def write_checksums(root: Path, target: Path) -> dict:
    prints = fingerprint(root)
    lines = "".join("%s  %s\n" % (prints[rel], rel) for rel in sorted(prints))
    target.write_text(lines, encoding="utf-8")
    return prints


def read_checksums(path: Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        out[rel] = digest
    return out


def compare(expected: dict, actual: dict) -> Optional[str]:
    """None when identical, or a plain sentence naming the first problem."""
    if len(expected) != len(actual):
        return "file count differs: expected %d, found %d" % (len(expected), len(actual))
    missing = sorted(set(expected) - set(actual))
    if missing:
        return "missing %d file(s), first is %s" % (len(missing), missing[0])
    extra = sorted(set(actual) - set(expected))
    if extra:
        return "%d unexpected file(s), first is %s" % (len(extra), extra[0])
    bad = sorted(rel for rel in expected if expected[rel] != actual[rel])
    if bad:
        return "%d file(s) do not match, first is %s" % (len(bad), bad[0])
    return None


def _make_writable(root: Path) -> None:
    """Give the owner write permission back across a freshly copied tree."""
    import stat
    for dirpath, dirs, files in os.walk(root):
        for name in dirs + files:
            target = Path(dirpath) / name
            try:
                target.chmod(target.stat().st_mode | stat.S_IWUSR)
            except OSError:
                pass
    try:
        root.chmod(root.stat().st_mode | stat.S_IWUSR)
    except OSError:
        pass


# ------------------------------------------------------------- the guard ----
def _has_symlink_within_repo(path: Path) -> bool:
    """True if any step from the repo down to `path` is a symlink.

    Resolving both sides would make a symlink pointing at the approved place
    look identical to the approved place. This is what refuses that.
    """
    current = path
    repo = REPO.resolve()
    while True:
        if current.is_symlink():
            return True
        if current.resolve() == repo or current.parent == current:
            return False
        current = current.parent


def _approved_path(role: str, configured) -> Path:
    """The configured path, only if it is exactly the approved location."""
    if not isinstance(configured, str) or not configured.strip():
        raise DemoError("demo configuration is missing a path for %r" % role)
    if Path(configured).is_absolute():
        raise DemoError("demo path for %r must be relative to the project" % role)

    approved = (REPO / APPROVED[role])
    candidate = (REPO / configured)
    if _has_symlink_within_repo(candidate) or _has_symlink_within_repo(approved):
        raise DemoError("demo path for %r goes through a link" % role)
    if candidate.resolve() != approved.resolve():
        raise DemoError("demo path for %r is not the approved location" % role)
    return approved.resolve()


def config() -> Optional[dict]:
    """The validated demo configuration, or None. Never raises.

    Anything wrong at all means no demo mode: no button, no endpoint,
    nothing changed.
    """
    try:
        if not CONFIG.is_file():
            return None
        raw = json.loads(CONFIG.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("demo_mode") is not True:
            return None

        paths = {role: _approved_path(role, raw.get(role)) for role in APPROVED}

        # Four distinct places, none inside another. A staging folder that
        # sat inside the working folder would be moved along with it.
        for a in paths:
            for b in paths:
                if a == b:
                    continue
                if paths[a] == paths[b]:
                    return None
                try:
                    paths[a].relative_to(paths[b])
                    return None
                except ValueError:
                    pass

        repo = REPO.resolve()
        if any(p == repo or p == (repo / "app") for p in paths.values()):
            return None
        if not paths["baseline"].is_dir() or not paths["working"].is_dir():
            return None
        if not (paths["baseline"].parent / CHECKSUM_NAME).is_file():
            return None
        return paths
    except (DemoError, ValueError, OSError):
        return None


def enabled() -> bool:
    return config() is not None


def status() -> dict:
    """All a screen is told: whether the button should be there."""
    return {"demo_mode": enabled()}


# ------------------------------------------------------------- the reset ----
def reset() -> dict:
    """Put the working folder back to the baseline. Steps in a fixed order.

    Nothing moves until a verified replacement is staged. A successful reset
    leaves no backup behind. A failed one may leave a single rollback copy,
    and says exactly where it is.
    """
    paths = config()
    if paths is None:
        raise DemoError("demo mode is not configured")

    baseline, working = paths["baseline"], paths["working"]
    staging_root, rollback = paths["staging"], paths["rollback"]
    staged = staging_root / working.name

    report = {"working": str(working), "baseline": str(baseline),
              "rollback": None, "staging": None, "working_in_place": True}

    # An old rollback means a previous reset failed and was never dealt with.
    if rollback.exists():
        raise DemoError(
            "a rollback copy from an earlier failed reset is still there; "
            "deal with it before resetting again",
            {**report, "rollback": str(rollback)})

    # 2. the baseline is what it was when it was frozen
    expected = read_checksums(baseline.parent / CHECKSUM_NAME)
    problem = compare(expected, fingerprint(baseline))
    if problem:
        raise DemoError("the baseline does not match its checksums: %s" % problem, report)

    # 3 and 4. stage a replacement and check it before anything is moved
    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_root.mkdir(parents=True)
    try:
        shutil.copytree(baseline, staged)
        # The baseline is held read-only so nothing can write into the
        # evidence. copytree carries those bits across, which would hand back
        # a working folder the app cannot save a caption into. Give the copy
        # its write bit back; the baseline itself is untouched.
        _make_writable(staged)
        problem = compare(expected, fingerprint(staged))
        if problem:
            raise DemoError("the staged copy did not come out right: %s" % problem, report)
    except DemoError:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise
    except OSError as exc:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise DemoError("could not stage a replacement: %s" % exc, report)

    # 5. the working folder moves aside, in one rename
    rollback.parent.mkdir(parents=True, exist_ok=True)
    working.rename(rollback)
    report["rollback"] = str(rollback)
    report["working_in_place"] = False

    # 6. and the verified replacement takes its place
    try:
        staged.rename(working)
    except OSError as exc:
        report["staging"] = str(staged)
        raise DemoError("the replacement could not be put in place: %s" % exc, report)
    report["working_in_place"] = True
    shutil.rmtree(staging_root, ignore_errors=True)

    # 7. and it is checked again where it now lives
    problem = compare(expected, fingerprint(working))
    if problem:
        raise DemoError("the restored folder does not match the baseline: %s" % problem, report)

    # 8. only the two demo settings, never the key file
    workspace.forget_demo_state(working)

    # 9. nothing accumulates after a reset that worked
    shutil.rmtree(rollback.parent, ignore_errors=True)
    report["rollback"] = None
    report["files"] = len(expected)
    report["baseline_checksum"] = aggregate(expected)
    return report

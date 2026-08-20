"""Build the Windows package Mark unzips. Committed, so it is repeatable.

Run from the repository root:

    python3 tools/package_windows.py --out build/windows

The four hand-typed commands this replaces were how `httpx` nearly went
missing. The plan named three binary dependencies; the real closure is nine
compiled packages and thirty-three distributions, and `anthropic` requires
`httpx` unconditionally, which an earlier revision called test-only. So this
script never carries a written list of what to install. It resolves the closure
from the pinned requirements and installs whatever that resolution produces.

Two things it will not do. It does not download anything unless asked, so the
runtime and the wheels are fetched once and reused. And it fails loudly rather
than shipping something wrong: a missing `dist`, a `dist` older than `src`, a
wheel that has no Windows build, or a package that does not verify against its
own manifest all stop the build.

Nothing here runs on Mark's machine. This is a development tool, and it is not
in the package it produces.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "app" / "server"))

import packaging  # noqa: E402

# Decided by the Task 1 evidence, recorded in Section 7b of the pilot plan.
# python.org stops publishing Windows embeddable builds when a series leaves
# bugfix support, so 3.9 through 3.12 are all missing security releases and
# 3.13 is close to the same cliff. Not chosen for being newest.
PYTHON_VERSION = "3.14.7"
PYTHON_TAG = "314"
PYTHON_ABI = "cp314"
EMBED_URL = ("https://www.python.org/ftp/python/%s/python-%s-embed-amd64.zip"
             % (PYTHON_VERSION, PYTHON_VERSION))

# Test-only. Everything else in requirements.txt ships, including httpx, which
# anthropic requires at runtime.
TEST_ONLY = ("pytest", "httpx-mock")

# Copied into the package as-is. app/tests, app/web/src, node_modules, demo.py
# and everything else on the plan's exclusion list is simply never named here.
APP_PARTS = ("data", "engine", "server", "templates")

SKIP_SERVER_FILES = {"demo.py"}


def say(message: str) -> None:
    print("  %s" % message)


def run(command, **kwargs) -> None:
    print("  $ %s" % " ".join(str(c) for c in command))
    subprocess.run(command, check=True, **kwargs)


def runtime_requirements(work: Path) -> Path:
    """The pinned set with the test-only lines removed, written for pip.

    The repository's own requirements.txt is never edited. This is a copy, and
    it lives in the build folder.
    """
    source = (REPO / "app" / "server" / "requirements.txt").read_text(encoding="utf-8")
    kept = []
    for line in source.splitlines():
        bare = line.strip()
        if not bare or bare.startswith("#"):
            continue
        name = bare.split("==")[0].split("[")[0].strip().lower()
        if name in TEST_ONLY:
            continue
        kept.append(bare)
    path = work / "runtime-requirements.txt"
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return path


# The environment the wheels will actually run in. pip on this Mac evaluates
# environment markers against the machine it is running on, not against
# --platform, so `uvloop; sys_platform != "win32"` reads as required here and
# the download fails on a package that has no Windows build at all. Evaluating
# the markers ourselves against these values is what makes the resolution the
# one Windows would do.
WINDOWS_ENV = {
    "sys_platform": "win32", "platform_system": "Windows", "os_name": "nt",
    "platform_machine": "AMD64", "platform_python_implementation": "CPython",
    "implementation_name": "cpython",
    "python_version": ".".join(PYTHON_VERSION.split(".")[:2]),
    "python_full_version": PYTHON_VERSION,
    "platform_release": "", "platform_version": "",
}


def _markers():
    """packaging's marker and requirement parsers, whichever copy is present.

    pip vendors them and pip is certainly installed, since this script shells
    out to it. A standalone packaging is preferred when it is there.
    """
    try:
        from packaging.markers import Marker
        from packaging.requirements import Requirement
    except ImportError:
        from pip._vendor.packaging.markers import Marker
        from pip._vendor.packaging.requirements import Requirement
    return Marker, Requirement


def _wheel_requires(wheel: Path):
    """Requires-Dist lines from a wheel's own METADATA, and its name."""
    import zipfile

    with zipfile.ZipFile(wheel) as archive:
        meta = [n for n in archive.namelist()
                if n.endswith(".dist-info/METADATA")][0]
        text = archive.read(meta).decode("utf-8", "replace")
    requires, name = [], ""
    for line in text.splitlines():
        if line.startswith("Requires-Dist:"):
            requires.append(line.split(":", 1)[1].strip())
        elif line.startswith("Name:") and not name:
            name = line.split(":", 1)[1].strip()
        elif not line.strip():
            break
    return name, requires


def resolve_closure(reqs_path: Path, wheels: Path) -> list:
    """Download the whole runtime closure, deriving it from wheel metadata.

    One requirement at a time with --no-deps, then its own Requires-Dist read
    back out of the wheel and filtered through the Windows environment above.
    Repeated until nothing new appears.

    Written this way rather than as `pip download -r requirements.txt` for two
    reasons. pip's marker evaluation on this Mac asks for uvloop, which is
    POSIX-only and has no Windows wheel, so the one-shot form simply fails.
    And a hand-written list of what to install is how `httpx` nearly went
    missing: the plan called it test-only when `anthropic` requires it
    unconditionally. Nothing here is written by hand; it all comes out of the
    metadata of the wheels themselves.
    """
    Marker, Requirement = _markers()
    pending = [line.strip() for line in
               reqs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    seen, ordered = set(), []

    while pending:
        raw = pending.pop(0)
        req = Requirement(raw)
        key = (req.name.lower().replace("_", "-"), tuple(sorted(req.extras)))
        if key in seen:
            continue
        seen.add(key)

        before = set(wheels.glob("*.whl"))
        run([sys.executable, "-m", "pip", "download", str(req).split(";")[0],
             "--no-deps", "--platform", "win_amd64",
             "--python-version", PYTHON_TAG, "--abi", PYTHON_ABI,
             "--implementation", "cp", "--only-binary=:all:", "-d", str(wheels)])
        fresh = sorted(set(wheels.glob("*.whl")) - before)
        ordered.extend(fresh)

        for wheel in (fresh or [w for w in wheels.glob("*.whl")
                                if w.name.lower().startswith(
                                    req.name.lower().replace("-", "_"))][:1]):
            _, requires = _wheel_requires(wheel)
            for line in requires:
                try:
                    dep = Requirement(line)
                except Exception:
                    continue
                if dep.marker is not None:
                    wanted = False
                    for extra in (sorted(req.extras) or [""]):
                        env = dict(WINDOWS_ENV)
                        env["extra"] = extra
                        if dep.marker.evaluate(env):
                            wanted = True
                            break
                    if not wanted:
                        continue
                pending.append(line.split(";")[0].strip())

    return sorted(wheels.glob("*.whl"))


def fetch_runtime(work: Path) -> Path:
    zip_path = work / ("python-%s-embed-amd64.zip" % PYTHON_VERSION)
    if zip_path.is_file():
        say("embeddable runtime already downloaded")
        return zip_path
    say("downloading %s" % EMBED_URL)
    with urllib.request.urlopen(EMBED_URL, timeout=120) as response:
        zip_path.write_bytes(response.read())
    return zip_path


def enable_site_packages(python_dir: Path) -> None:
    """Make the embedded interpreter look in site-packages.

    The embeddable distribution's import path is governed by its `._pth` file
    and it ignores site-packages until told otherwise. The directory is added
    as a literal line rather than by uncommenting `import site`, because the
    line is what actually puts it on sys.path and needs nothing else to work.
    Whether this behaves as intended on Windows is a Gate A observation, not
    something this script can prove from a Mac.
    """
    found = sorted(python_dir.glob("python*._pth"))
    if not found:
        raise SystemExit("no ._pth file in the embeddable runtime")
    path = found[0]
    lines = path.read_text(encoding="utf-8").splitlines()
    if "site-packages" not in lines:
        lines.append("site-packages")
    if "import site" not in lines:
        lines.append("import site")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    say("%s now lists site-packages" % path.name)


def check_web_build() -> Path:
    """The built interface must be there and must not be stale."""
    dist = REPO / "app" / "web" / "dist"
    index = dist / "index.html"
    if not index.is_file():
        raise SystemExit(
            "app/web/dist is missing. Run: cd app/web && npm ci && npm run build")
    newest_source = max((p.stat().st_mtime for p in (REPO / "app" / "web" / "src").rglob("*")
                         if p.is_file()), default=0)
    if index.stat().st_mtime < newest_source:
        raise SystemExit(
            "app/web/dist is older than app/web/src. Rebuild it before packaging:\n"
            "    cd app/web && npm ci && npm run build")
    return dist


def copy_app(out: Path) -> None:
    app_out = out / "app"
    app_out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO / "app" / "run_app.py", app_out / "run_app.py")

    for part in APP_PARTS:
        source = REPO / "app" / part
        target = app_out / part
        shutil.copytree(
            source, target,
            ignore=shutil.ignore_patterns(*packaging.NOISE_DIRS, *packaging.NOISE_FILES,
                                          "*.pyc", "*.env"))
    for name in SKIP_SERVER_FILES:
        gone = app_out / "server" / name
        if gone.is_file():
            gone.unlink()
            say("excluded app/server/%s" % name)

    shutil.copytree(check_web_build(), app_out / "web" / "dist")


def add_demo_job(out: Path) -> Path:
    """The practice job, generated fresh into the package.

    Generated rather than copied, so nothing from `Report Examples/`,
    `locker/`, the development `RRF Demo Jobs/` or any client folder can reach
    it even by accident. It is not the development demo system: `demo.py`,
    `/api/demo` and Reset Demo are still excluded, and this job is not marked
    AI safe.
    """
    import demo_job

    return demo_job.build(out)


def build(out: Path, work: Path, offline: bool) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    work.mkdir(parents=True, exist_ok=True)

    print("Roy R. Fisher package")
    print("  version %s, CPython %s" % (packaging.version_of(REPO), PYTHON_VERSION))

    say("copying the app")
    copy_app(out)
    shutil.copy2(REPO / "VERSION", out / "VERSION")
    shutil.copy2(REPO / "Start Roy R. Fisher.bat", out / "Start Roy R. Fisher.bat")
    (out / "README FIRST.txt").write_text(readme_text(), encoding="utf-8")

    python_dir = out / "python"
    python_dir.mkdir()
    if not offline:
        shutil.unpack_archive(str(fetch_runtime(work)), str(python_dir))
        enable_site_packages(python_dir)

        wheels = work / "wheels"
        wheels.mkdir(exist_ok=True)
        reqs = runtime_requirements(work)
        say("resolving the runtime closure for win_amd64 from wheel metadata")
        downloaded = resolve_closure(reqs, wheels)
        if not downloaded:
            raise SystemExit("no wheels were downloaded, so there is nothing to install")
        say("installing %d wheels into the package" % len(downloaded))
        # Every wheel the resolution produced, by name, rather than resolving a
        # second time from the requirements file. Resolving twice is how a
        # transitive dependency goes missing: `pip install -r` with `--no-deps`
        # would install the nine pinned lines and none of the twenty-four
        # packages they pull, and `httpx` is one of those.
        run([sys.executable, "-m", "pip", "install", "--no-index",
             "--find-links", str(wheels), "--target",
             str(python_dir / "site-packages"),
             "--platform", "win_amd64", "--python-version", PYTHON_TAG,
             "--abi", PYTHON_ABI, "--implementation", "cp",
             "--only-binary=:all:", "--no-deps", "--upgrade",
             # No byte-compilation, for two reasons that both matter.
             # Any .pyc produced here is compiled by this Mac's Python 3.9 and
             # is useless to a Windows 3.14 interpreter. And pip records the
             # paths of the files it compiled into each RECORD, which on this
             # machine are absolute paths through Spenser's own home folder
             # and a randomly named temporary directory. That leaked his
             # username into every package and changed the bytes on every
             # build, so the archive could never have had a stable hash.
             "--no-compile",
             # The wheels were already resolved for cp314 above. pip checks
             # Requires-Python against the interpreter running this script,
             # not against --python-version, so a package needing >=3.10 is
             # refused by a 3.9 pip even though it will never run under it.
             "--ignore-requires-python"]
            + [str(w) for w in downloaded])
    else:
        say("offline: runtime and wheels skipped, layout and manifest only")

    say("generating the practice job")
    add_demo_job(out)

    say("removing build-machine traces from the installed metadata")
    strip_local_traces(python_dir / "site-packages")

    say("writing the manifest")
    (out / packaging.MANIFEST_NAME).write_text(packaging.build_manifest(out),
                                               encoding="utf-8")

    say("verifying the package against its own manifest")
    packaging.verify(out)

    listed = packaging.read_manifest(out)

    say("making the archive")
    zip_path = out.with_name(out.name + ".zip")
    make_zip(out, zip_path)
    sidecar = write_sidecar(zip_path)

    say("extracting it somewhere new and checking it")
    checked = verify_zip(out, zip_path)

    print()
    print("Built %s" % out)
    print("  files      %d" % len(listed["files"]))
    print("  aggregate  %s" % listed["aggregate"])
    print()
    print("Archive %s" % zip_path.name)
    print("  size       %.1f MB" % (zip_path.stat().st_size / (1024 * 1024)))
    print("  entries    %d" % checked["entries"])
    print("  sha256     %s" % sha256_of(zip_path))
    print("  sidecar    %s" % sidecar.name)
    print("  extracted  %s" % checked["manifest"])
    print()
    print("This extraction was done on the Mac with Python's zipfile. It is not")
    print("the Gate A test, which needs a browser download and Windows Explorer.")


# ----------------------------------------------------------------- the zip --
# The ZIP epoch. Every entry is stamped with this instead of its real mtime, so
# two builds from the same inputs produce the same bytes. 1980-01-01 is the
# earliest a ZIP can express, and any fixed value would do; what matters is
# that it is fixed.
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

# Stamped on every entry rather than copied from disk, for the same reason.
FILE_MODE = 0o644
DIR_MODE = 0o755


class UnsafeArchivePath(Exception):
    """Something in the tree would not be safe to write on extraction."""


def _arcname(root: Path, path: Path, top: str) -> str:
    """The name this file gets inside the archive, checked before it is used.

    Every entry has to land inside the one top-level folder. An absolute path,
    a parent traversal, or a backslash that Windows would read as a separator
    are all refused here rather than trusted to the extractor, because the
    extractor is Mark's copy of Explorer and not something we control.
    """
    rel = path.relative_to(root).as_posix()
    name = "%s/%s" % (top, rel)
    if rel.startswith("/") or ":" in rel or "\\" in rel:
        raise UnsafeArchivePath("unsafe path in the package: %s" % rel)
    parts = name.split("/")
    if ".." in parts or "" in parts[1:]:
        raise UnsafeArchivePath("unsafe path in the package: %s" % rel)
    if parts[0] != top:
        raise UnsafeArchivePath("path escapes the top folder: %s" % rel)
    return name


def _entries(root: Path):
    """Every file, and any directory that would otherwise be lost, sorted.

    Sorted so the archive is deterministic. Empty directories get an explicit
    entry because nothing else would carry them, and the extraction check
    compares trees.
    """
    root = Path(root)
    files, empties = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in packaging.NOISE_DIRS)
        here = Path(dirpath)
        keep = [f for f in sorted(filenames)
                if f not in packaging.NOISE_FILES
                # runtime.json is written at startup and is outside the
                # immutable set. An archived one would carry a port from
                # another machine into Mark's copy. verify_zip refuses it too,
                # so this is the first of two doors rather than the only one.
                and not (here == Path(root) and f == packaging.RUNTIME_NAME)
                # The archive and its sidecar are siblings of this folder, not
                # inside it, so they cannot be walked. Scoped to the top level
                # anyway, and only there: python/python314.zip is the embedded
                # standard library and dropping it broke the build once.
                and not (here == Path(root) and f.endswith((".zip", ".sha256")))]
        if not keep and not dirnames and here != root:
            empties.append(here)
        files.extend(here / f for f in keep)
    return sorted(files), sorted(empties)


def make_zip(folder: Path, zip_path: Path) -> None:
    """One archive, one top-level folder, byte-identical between builds.

    Written here rather than shelled out to `zip` or made in Finder, because
    both stamp real timestamps and Finder adds its own metadata files. The
    archive Spenser approves has to be the archive the hash names, and that
    means the bytes cannot drift between two runs of the same build.
    """
    folder = Path(folder)
    top = folder.name
    files, empties = _entries(folder)

    for path in files + empties:
        if path.is_symlink():
            raise UnsafeArchivePath(
                "the package contains a link, which is never archived: %s"
                % path.relative_to(folder))

    if zip_path.exists():
        zip_path.unlink()

    # One sorted pass over files and empty directories together, so the order
    # inside the archive is the sorted order of the names and does not depend
    # on which kind of entry came first.
    planned = sorted(
        [(_arcname(folder, p, top), p, False) for p in files]
        + [(_arcname(folder, p, top) + "/", p, True) for p in empties])

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for name, path, is_dir in planned:
            info = zipfile.ZipInfo(name, ZIP_EPOCH)
            info.create_system = 3
            if is_dir:
                info.external_attr = (DIR_MODE << 16) | 0x10
                archive.writestr(info, b"")
            else:
                info.external_attr = FILE_MODE << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sidecar(zip_path: Path) -> Path:
    """The conventional `sha256sum` line: hash, two spaces, filename.

    This names the exact artifact so Spenser can approve one build rather than
    a build. It is never a step for Mark: the launcher checks the package's own
    MANIFEST after he unzips, and he is never asked to compare anything.
    """
    sidecar = zip_path.with_name(zip_path.name + ".sha256")
    sidecar.write_text("%s  %s\n" % (sha256_of(zip_path), zip_path.name),
                       encoding="utf-8")
    return sidecar


def verify_zip(folder: Path, zip_path: Path) -> dict:
    """Extract the archive somewhere new and prove it is the package.

    This is a Mac extraction with Python's own zipfile. It does not stand in
    for Gate A, which needs the archive downloaded through a browser and
    unzipped by Windows Explorer on Mark's kind of machine, with SmartScreen
    watching. Nothing here says anything about that.
    """
    folder = Path(folder)
    top = folder.name
    facts = {}

    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        facts["entries"] = len(names)

        tops = {n.split("/")[0] for n in names}
        if tops != {top}:
            raise UnsafeArchivePath(
                "the archive must hold exactly one folder, found: %s" % sorted(tops))
        for name in names:
            if name.startswith("/") or ".." in name.split("/"):
                raise UnsafeArchivePath("unsafe path in the archive: %s" % name)
            if not name.startswith(top + "/"):
                raise UnsafeArchivePath("path escapes the top folder: %s" % name)
        if any(n.endswith("/" + packaging.RUNTIME_NAME) for n in names):
            raise UnsafeArchivePath(
                "%s is created at startup and must never be archived"
                % packaging.RUNTIME_NAME)

        holder = tempfile.mkdtemp(prefix="rrf-zip-check-")
        try:
            archive.extractall(holder)
            extracted = Path(holder) / top

            packaging.verify(extracted)
            facts["manifest"] = "the extracted package validates against its own MANIFEST"

            if packaging.aggregate(extracted) != packaging.aggregate(folder):
                raise UnsafeArchivePath(
                    "the extracted package does not match the folder it came from")
            facts["matches_folder"] = True
        finally:
            shutil.rmtree(holder, ignore_errors=True)
    return facts


def strip_local_traces(site_packages: Path) -> int:
    """Delete the pip metadata that records where the wheels came from.

    `direct_url.json` is optional PEP 610 metadata naming the exact file a
    distribution was installed from. Installing from a local directory writes
    an absolute `file:///Users/...` URL into it, so every one of these carries
    the build machine's username and folder layout into the package Mark
    unzips. Nothing reads them at runtime.

    They are also why two different machines could never produce the same
    archive, even after the byte-compilation fix, because the path differs per
    machine rather than per build.
    """
    removed = 0
    for found in sorted(Path(site_packages).glob("*.dist-info/direct_url.json")):
        found.unlink()
        removed += 1
    return removed


def readme_text() -> str:
    return (
        "Roy R. Fisher\n"
        "=============\n"
        "\n"
        "1. Unzip this folder somewhere in your own account, for example your\n"
        "   Desktop or your Documents folder. Do not put it in Program Files.\n"
        "\n"
        "2. Double-click \"Start Roy R. Fisher.bat\".\n"
        "\n"
        "3. Your browser opens by itself. Leave the black window open while you\n"
        "   work. To stop the app, close that window.\n"
        "\n"
        "Trying it out\n"
        "-------------\n"
        "\n"
        "This package comes with a practice job so you can try everything\n"
        "straight away.\n"
        "\n"
        "1. Start the app.\n"
        "2. When it asks where your jobs live, choose the \"Demo Jobs\" folder\n"
        "   inside this one.\n"
        "3. Open the job called \"ANYTOWN_100 Example Avenue - 2026\".\n"
        "4. Go to its Photos folder and build a Subject Photographs document.\n"
        "\n"
        "That job and all twelve of its photographs are made up. There is no\n"
        "real property, no client and no personal information in any of it,\n"
        "and nothing in it is sent anywhere. Practise on it as much as you\n"
        "like. When you want to work on a real job, start the app again and\n"
        "point it at your own jobs folder instead.\n"
        "\n"
        "Windows may say it protected your PC the first time. Click More info,\n"
        "then Run anyway. Spenser will be on the call the first time.\n"
        "\n"
        "Keep the previous version's folder until this one has worked once.\n"
        "Only one version can run at a time.\n"
        "\n"
        "If anything goes wrong, the black window says what happened. Send\n"
        "Spenser a photo of it and do not delete the folder.\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="build/windows/Roy R. Fisher v%s"
                        % packaging.version_of(REPO))
    parser.add_argument("--work", default="build/cache",
                        help="downloaded runtime and wheels, reused between builds")
    parser.add_argument("--offline", action="store_true",
                        help="layout and manifest only, no downloads")
    args = parser.parse_args()

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO / out
    work = Path(args.work)
    if not work.is_absolute():
        work = REPO / work

    build(out, work, args.offline)
    return 0


if __name__ == "__main__":
    sys.exit(main())

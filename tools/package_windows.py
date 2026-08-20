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
import shutil
import subprocess
import sys
import urllib.request
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
             # The wheels were already resolved for cp314 above. pip checks
             # Requires-Python against the interpreter running this script,
             # not against --python-version, so a package needing >=3.10 is
             # refused by a 3.9 pip even though it will never run under it.
             "--ignore-requires-python"]
            + [str(w) for w in downloaded])
    else:
        say("offline: runtime and wheels skipped, layout and manifest only")

    say("writing the manifest")
    (out / packaging.MANIFEST_NAME).write_text(packaging.build_manifest(out),
                                               encoding="utf-8")

    say("verifying the package against its own manifest")
    packaging.verify(out)

    listed = packaging.read_manifest(out)
    print()
    print("Built %s" % out)
    print("  files     %d" % len(listed["files"]))
    print("  aggregate %s" % listed["aggregate"])


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

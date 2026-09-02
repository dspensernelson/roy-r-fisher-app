"""Serve a pretend update, so the update screens can be walked on the Mac.

Spenser cannot see the update screens on his own machine. His Mac runs the
source code rather than a package, so the app answers "no update" and the
button never appears. `RRF_UPDATE_IN_CHECKOUT` makes the button appear; this
gives it something to find.

It builds a small package, hashes it, writes the pointer file, and serves all
three over a local address. Nothing here touches the real bucket, and nothing
here is in the package. It is a development tool.

**What walking it on the Mac proves.** The screens: the notice, the step, the
bar counting megabytes, Cancel, the closing message, and the failure messages.
It also proves the download, the hash check and the manifest check, because
those are the same code on both machines.

**What it does not prove.** Anything about Windows. The real installer never
runs: the package this builds carries a stand-in in place of the Windows
Python, which prints a line and stops. So the app closes itself the way it
will on Mark's machine, and then nothing is installed, which is the one place
this deliberately stops short.

Run it from the repository root:

    python3 tools/fake_update.py

Then, in another window:

    RRF_UPDATE_IN_CHECKOUT=1 RRF_UPDATE_BUCKET=http://127.0.0.1:8777 \\
        python3 app/run_app.py
"""
import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import zipfile
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "app" / "server"))

import packaging  # noqa: E402

PORT = 8777

# What the stand-in for python.exe prints when the handoff starts it. It is a
# shell script, because this runs on a Mac. On Windows the real embedded
# interpreter sits here and actually installs.
STAND_IN = """#!/bin/sh
echo
echo "  This is the stand-in installer, not the real one."
echo "  On Mark's PC the real one installs the update here."
echo "  Nothing has been installed. Close this window."
echo
sleep 5
"""


def build_package(where, version):
    """A package with the shape of a real one, and a manifest over all of it."""
    top = where / ("Roy R. Fisher v%s" % version)
    program = top / packaging.PROGRAM_DIR
    (program / "app" / "server").mkdir(parents=True)
    (program / "python").mkdir(parents=True)

    (program / "VERSION").write_text(version + "\n", encoding="utf-8")
    (top / "Start Roy R. Fisher.bat").write_text("@echo off\r\n", encoding="utf-8")
    (top / "README FIRST.txt").write_text(
        "This is a practice package. It installs nothing.\n", encoding="utf-8")

    for name in ("run_app.py", "install_windows.py", "update_apply.py"):
        shutil.copy2(REPO / "app" / name, program / "app" / name)
    shutil.copy2(REPO / "app" / "server" / "packaging.py",
                 program / "app" / "server" / "packaging.py")

    stand_in = program / "python" / "python.exe"
    stand_in.write_text(STAND_IN, encoding="utf-8")
    stand_in.chmod(stand_in.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)

    (program / packaging.MANIFEST_NAME).write_text(
        packaging.build_manifest(program), encoding="utf-8")
    packaging.verify(program)
    return top


def make_zip(folder, zip_path):
    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(Path(folder).rglob("*")):
            if path.is_file():
                archive.write(str(path), "%s/%s" % (
                    folder.name, path.relative_to(folder).as_posix()))
    return zip_path


def publish(where, version, damage):
    """Write the three files the app reads, into one folder."""
    where.mkdir(parents=True, exist_ok=True)
    built = build_package(where / "tree", version)
    zip_path = make_zip(built, where / (built.name + ".zip"))

    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    if damage == "hash":
        # A checksum that does not match, to walk the failure message.
        digest = "b" * 64
    if damage == "zip":
        # A truncated download, which is what an interrupted transfer leaves.
        body = zip_path.read_bytes()
        zip_path.write_bytes(body[:len(body) // 2])

    (where / (zip_path.name + ".sha256")).write_text(
        "%s  %s\n" % (digest, zip_path.name), encoding="utf-8")
    (where / "latest.json").write_text(json.dumps(
        {"version": version, "zip": zip_path.name,
         "size": zip_path.stat().st_size}, indent=2) + "\n", encoding="utf-8")
    shutil.rmtree(where / "tree", ignore_errors=True)
    return zip_path


def serve(where, port):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(where), **kwargs)

        def log_message(self, fmt, *args):
            print("  asked for %s" % (args[0] if args else fmt))

    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", default="",
                        help="the version to offer (default: one above this repo)")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--damage", choices=("hash", "zip"), default="",
                        help="publish a broken update, to walk a failure")
    args = parser.parse_args()

    version = args.version
    if not version:
        parts = packaging.version_of(REPO).split(".")
        parts[-1] = str(int(parts[-1]) + 1) if parts[-1].isdigit() else "1"
        version = ".".join(parts)

    where = REPO / "build" / "fake-bucket"
    shutil.rmtree(where, ignore_errors=True)
    zip_path = publish(where, version, args.damage)

    print()
    print("Offering version %s, %.1f MB" % (version,
                                            zip_path.stat().st_size / (1024 * 1024)))
    if args.damage:
        print("Deliberately broken: %s" % args.damage)
    print("Serving %s on http://127.0.0.1:%d" % (where, args.port))
    print()
    print("Start the app in another window with:")
    print()
    print("    RRF_UPDATE_IN_CHECKOUT=1 RRF_UPDATE_BUCKET=http://127.0.0.1:%d \\"
          % args.port)
    print("        python3 app/run_app.py")
    print()
    print("Press Control and C here when you are finished.")
    print()
    try:
        serve(where, args.port)
    except KeyboardInterrupt:
        print()
        print("Stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

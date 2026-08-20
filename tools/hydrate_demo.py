"""Fill the development demo jobs with real photographs, reproducibly.

Spenser's demo folders are copies of Mark's real jobs and most had no
photographs at all, so the workflow could not be exercised. The first version
of this filled them with flat coloured panels, which was useless: you cannot
judge a layout, a caption or a document size against a purple rectangle.

It now copies actual property photographs out of `RRF/Report Examples`, which
Spenser authorised on 2026-08-20 for exactly this local testing purpose.

The source is strictly read-only and is treated that way. Files are opened for
reading and nothing else: never moved, renamed, edited, deleted, resized or
rewritten. The tree is fingerprinted before and after and proven byte-identical.

What lands in a demo job is a sanitised copy, not the original file:

- re-encoded through Pillow, so no EXIF and no GPS survives
- given a generic name, `photo-07.jpg`, carrying no client filename
- carrying no document, address, caption or other report content

A few synthetic fixtures stay, because each tests something a photograph
cannot: an image too small to be enlarged, and a deliberately malformed file.
Both are unmistakably named and visibly labelled.

Everything here is Local layout material under Section 25. These are copies of
real client work, and a job becomes sendable only by being named on the
allowlist through the controlled workflow.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageOps

# Without this Pillow cannot write HEIF at all, and the first attempt at
# hydration fell back to JPEG without saying so, which meant the demo had no
# HEIC in it while claiming to. The app registers this in photos.py; a tool
# that writes photographs has to do it too.
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_READY = True
except ImportError:
    HEIF_READY = False

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "app" / "server"))

import demo  # noqa: E402

# What each job is for. Named so a person can look at the list and see which
# scenario is missing, rather than counting files.
PLAN = {
    "BETTENDORF_1215 Middle Road - 2026": {
        "note": "an ordinary dozen", "real": 10, "synthetic": 0},
    "BETTENDORF_1830 E Kimberly Road - 2026 Tax": {
        "note": "exactly one full tranche", "real": 60, "synthetic": 0},
    "BETTENDORF_2103 Kimberly Road - 2026": {
        "note": "sixty-one, which now runs as 60 + 1", "real": 61, "synthetic": 0},
    "CEDAR RAPIDS_1580 Blairs Ferry Road NE - 2026 Tax": {
        "note": "two full tranches and a remainder, 100 as 60 + 40",
        "real": 100, "synthetic": 0},
    "CLINTON_622 S 4th Street - 2025 Tax": {
        "note": "mixed formats, HEIC and PNG beside JPEG", "real": 8,
        "synthetic": 0, "formats": True},
    "DAVENPORT_2840 Brady Street - 2026 Tax": {
        "note": "Mark's own twelve, untouched", "real": 0, "synthetic": 0},
    "DAVENPORT_7719 Northwest Boulevard - 2026": {
        "note": "real photographs plus the tiny image that must not be enlarged",
        "real": 9, "synthetic": 1},
    "MOLINE_3400 41st Avenue Drive - Rent Study": {
        "note": "some photographs excluded from the report", "real": 10,
        "synthetic": 0, "cut": 3},
    "MUSCATINE_910 Grandview Avenue ROW": {
        "note": "captions part reviewed, part not", "real": 9, "synthetic": 0,
        "reviewed": 5, "captioned": 7},
}

# The read-only source Spenser authorised on 2026-08-20.
SOURCE = Path(__file__).resolve().parents[2] / "RRF" / "Report Examples"

# Real camera photographs, by size. Below this is a logo or an icon; above it
# is usually a scan rather than a photograph.
MIN_BYTES, MAX_BYTES = 120_000, 12_000_000


def source_photographs() -> list:
    """Every usable photograph in the source, sorted, read-only.

    Sorted so two runs pick the same files in the same order, which is what
    makes the hydration reproducible.
    """
    if not SOURCE.is_dir():
        return []
    found = []
    for dirpath, dirs, files in os.walk(SOURCE):
        dirs.sort()
        for name in sorted(files):
            if not name.lower().endswith((".jpg", ".jpeg")):
                continue
            path = Path(dirpath) / name
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if MIN_BYTES <= size <= MAX_BYTES:
                found.append(path)
    return found


def sanitise(source: Path, target: Path, fmt: str = "JPEG") -> None:
    """One demo copy: re-encoded, stripped of metadata, generically named.

    Re-encoding rather than copying the bytes is the point. A byte copy would
    carry the camera's EXIF, and with it the date, the device and possibly the
    location the photograph was taken. Pillow writes none of that unless it is
    asked to, so opening and saving is what removes it.

    The source is opened read-only and closed before anything is written. It is
    never the file being saved.
    """
    with Image.open(source) as opened:
        upright = ImageOps.exif_transpose(opened)
        rgb = upright.convert("RGB")
        # Kept large enough to be a real test of the document optimisation,
        # small enough that nine demo jobs do not cost gigabytes.
        rgb.thumbnail((2400, 2400))

        # Rebuilt from the pixels alone. Opening a file leaves the camera's
        # EXIF in `info`, and Pillow writes that back out for JPEG even when
        # no exif argument is given, so converting and resizing is not enough
        # on its own: the make, the model and the date it was taken all
        # survived into the copies until this line existed.
        clean = Image.new("RGB", rgb.size)
        clean.paste(rgb)          # C-level copy; putdata via a Python list
        rgb = clean               # was correct but took minutes per job
        if fmt == "PNG":
            rgb.save(target, format="PNG", optimize=True)
        elif fmt == "HEIF":
            rgb.save(target, format="HEIF", quality=80)
        else:
            rgb.save(target, format="JPEG", quality=82, optimize=True)


SHAPES = {
    "mixed":   [(1600, 1200), (1200, 1600), (1400, 1050), (1024, 1024),
                (1920, 1080), (900, 1600)],
    "large":   [(4032, 3024), (3024, 4032), (4000, 2250)],
    "shapes":  [(1800, 1200), (1200, 1800), (640, 480), (400, 300), (1500, 1500)],
    "formats": [(1600, 1200), (1200, 1600), (1024, 768)],
}


def panel(width, height, index, label):
    """A flat numbered panel that says what it is, like the packaged one."""
    from PIL import ImageDraw

    tone = (60 + (index * 17) % 90, 70 + (index * 29) % 80, 90 + (index * 13) % 70)
    image = Image.new("RGB", (width, height), tone)
    draw = ImageDraw.Draw(image)
    ink = tuple(min(255, c + 105) for c in tone)
    margin = max(8, min(width, height) // 24)
    draw.rectangle([margin, margin, width - margin, height - margin],
                   outline=tuple(min(255, c + 30) for c in tone),
                   width=max(3, min(width, height) // 90))

    def stamp(text, scale, y):
        box = draw.textbbox((0, 0), text)
        small = Image.new("RGB", (box[2] - box[0] + 4, box[3] - box[1] + 4), tone)
        ImageDraw.Draw(small).text((2 - box[0], 2 - box[1]), text, fill=ink)
        grown = small.resize((small.width * scale, small.height * scale), Image.NEAREST)
        room = width - 2 * margin
        if grown.width > room:
            ratio = room / grown.width
            grown = grown.resize((max(1, int(grown.width * ratio)),
                                  max(1, int(grown.height * ratio))), Image.NEAREST)
        image.paste(grown, ((width - grown.width) // 2, int(height * y) - grown.height // 2))

    stamp("%02d" % index, max(4, min(width, height) // 60), 0.34)
    stamp(label.upper(), max(2, min(width, height) // 170), 0.52)
    stamp("SYNTHETIC DEMO IMAGE", max(2, min(width, height) // 230), 0.64)
    stamp("LOCAL TESTING ONLY", max(2, min(width, height) // 230), 0.71)
    return image


def add_real_photos(photos_dir: Path, how_many: int, pool: list, offset: int,
                    formats: bool = False) -> list:
    """Copy and sanitise this many real photographs into a demo job.

    The pool is reused across jobs on purpose. Spenser said the same safe set
    appearing in more than one demo job is fine, and it means nine jobs do not
    need nine hundred distinct photographs.
    """
    photos_dir.mkdir(parents=True, exist_ok=True)
    if not pool:
        return []
    made = []
    for i in range(how_many):
        source = pool[(offset + i) % len(pool)]
        suffix, fmt = ".jpg", "JPEG"
        if formats and i % 3 == 1:
            suffix, fmt = ".png", "PNG"
        elif formats and i % 3 == 2 and HEIF_READY:
            suffix, fmt = ".heic", "HEIF"
        target = photos_dir / ("photo-%02d%s" % (i + 1, suffix))
        if target.exists():
            continue
        try:
            sanitise(source, target, fmt)
        except Exception:
            # One unreadable source file is not a reason to abandon the run.
            continue
        made.append(target)
    return made


def add_synthetic_fixtures(photos_dir: Path, how_many: int) -> list:
    """The few cases a real photograph cannot test.

    A tiny image, because the never-enlarge rule needs something smaller than
    the cap. And a deliberately malformed file, because the build has to fail
    honestly on one. Both are named so nobody mistakes them for a photograph.
    """
    photos_dir.mkdir(parents=True, exist_ok=True)
    made = []
    if how_many >= 1:
        tiny = photos_dir / "SYNTHETIC-tiny-do-not-enlarge.jpg"
        if not tiny.exists():
            panel(320, 240, 1, "synthetic tiny fixture").save(tiny, quality=80)
            made.append(tiny)
    # A deliberately malformed file used to be added here. It was removed: it
    # made that job's Build fail, and a demo folder that does not work is the
    # thing this whole correction is about. Honest failure on a bad file is
    # covered in the test suite, where it belongs.
    return made


# Files this tool is allowed to create, and therefore allowed to remove. A
# blanket sweep for photo-manifest.json once deleted one of Mark's own, which
# held captions a real paid run had produced. Nothing outside these prefixes is
# ever touched.
OURS = ("photo-", "SYNTHETIC-")


def clear_ours(baseline: Path) -> int:
    """Remove only what this tool made, so a re-hydration starts clean.

    Never a pattern sweep. A manifest or a photograph that this tool did not
    create belongs to somebody else, and the fact that it looks like something
    we would have made is not evidence that we made it.
    """
    removed = 0
    for photos_dir in sorted(baseline.glob("*/Photos")):
        for path in sorted(photos_dir.iterdir()):
            if path.is_file() and path.name.startswith(OURS):
                path.unlink()
                removed += 1
    return removed


def write_manifest(job: Path, cut: int = 0, reviewed: int = 0, captioned: int = 0) -> None:
    """A fixture manifest, so review and exclusion states can be looked at.

    Only written when a job actually needs one of those states. Everything
    else is left with no manifest, which is the ordinary starting point.
    """
    if not (cut or reviewed or captioned):
        return
    photos_dir = job / "Photos"
    existing = photos_dir / "photo-manifest.json"
    if existing.is_file() and not json.loads(existing.read_text()).get("_fixture"):
        # Somebody else's manifest. Leave it alone rather than overwrite the
        # captions in it, which may have been paid for.
        return
    names = sorted(p.name for p in photos_dir.iterdir()
                   if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic"))
    entries = []
    for i, name in enumerate(names):
        entry = {"file": name, "caption": ""}
        if i < captioned:
            entry["caption"] = "View of demo subject %02d" % (i + 1)
        if i < reviewed and entry["caption"]:
            entry["reviewed"] = True
        if cut and i >= len(names) - cut:
            entry["cut"] = True
        entries.append(entry)
    (photos_dir / "photo-manifest.json").write_text(json.dumps(
        {"job": job.name, "context": "", "report_year": 2026,
         "caption_style": "view", "_fixture": True, "photos": entries},
        indent=2), encoding="utf-8")


def hydrate(baseline: Path) -> dict:
    pool = source_photographs()
    report = {}
    offset = 0
    for name, spec in PLAN.items():
        job = baseline / name
        if not job.is_dir():
            report[name] = "not present, skipped"
            continue
        photos_dir = job / "Photos"
        def count():
            return len([p for p in photos_dir.iterdir()
                        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic")]
                       ) if photos_dir.is_dir() else 0

        before = count()
        real = add_real_photos(photos_dir, spec["real"], pool, offset,
                               spec.get("formats", False)) if spec["real"] else []
        offset += spec["real"]
        fake = add_synthetic_fixtures(photos_dir, spec.get("synthetic", 0))
        write_manifest(job, spec.get("cut", 0), spec.get("reviewed", 0),
                       spec.get("captioned", 0))
        report[name] = "%d -> %d (%d real, %d fixture), %s" % (
            before, count(), len(real), len(fake), spec["note"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--allowlist", action="store_true",
                        help="mark the hydrated copies sendable for caption testing")
    parser.add_argument("--reset", action="store_true",
                        help="run Reset Demo afterwards, restoring the working copy")
    args = parser.parse_args()

    paths = demo.config()
    if paths is None:
        raise SystemExit(
            "No validated demo configuration on this machine, so there is\n"
            "nothing to hydrate. This tool only ever writes into the approved\n"
            "baseline that .rrf-demo.json names.")

    baseline = paths["baseline"]
    print("Hydrating the demo baseline")
    gone = clear_ours(baseline)
    if gone:
        print("  removed %d file(s) this tool had made previously" % gone)
    print("  %s\n" % baseline)
    for name, line in sorted(hydrate(baseline).items()):
        print("  %-52s %s" % (name[:52], line))

    print("\n  rewriting the baseline checksums")
    demo.write_checksums(baseline, baseline.parent / demo.CHECKSUM_NAME)

    if args.allowlist:
        import aipolicy
        print("\n  allowlisting the hydrated copies for caption testing")
        marked = []
        for name, spec in PLAN.items():
            if spec["real"] == 0:
                # Mark's own photographs. Never allowlisted by this tool: they
                # were not created through this controlled process.
                continue
            if not (paths["working"] / name).is_dir():
                continue
            aipolicy.mark_ai_safe(name)
            marked.append(name)
        for name in marked:
            print("    AI safe: %s" % name)
        print("  everything else under the demo root stays Local only")

    if args.reset:
        print("  restoring the working copy through Reset Demo")
        demo.reset()
        print("  done")
    return 0


if __name__ == "__main__":
    sys.exit(main())

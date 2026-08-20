"""Fill the development demo jobs with photographs, reproducibly.

Spenser's demo folders are copies of Mark's real jobs, and most of them have
no photographs in them, so the workflow cannot be exercised end to end without
inventing something. This does the inventing.

Two things it deliberately does not do.

It never reads `Report Examples/`, `locker/`, or any client folder. Every
photograph it adds is drawn from nothing, the same way the packaged practice
job's are, so nothing client-derived can travel into a demo by accident. The
real photographs already sitting in three of these jobs are Mark's and are left
exactly as they are: this only ever adds files that were not there.

And it hydrates the **baseline**, not the working copy. `demo.reset()` replaces
the working folder wholesale from the baseline, so anything written straight
into the working folder is deleted the first time the reset button is pressed.
Hydrating the baseline and then resetting is what makes Reset Demo restore the
photographs instead of removing them.

Everything here is Local layout material under Section 25 of the pilot plan.
These jobs are copies of real client work; the policy defaults every job under
the validated demo root to Local only, and nothing in this file marks anything
AI safe.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image

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
        "note": "the ordinary twelve", "add": 10, "kind": "mixed"},
    "BETTENDORF_1830 E Kimberly Road - 2026 Tax": {
        "note": "exactly the sixty-photo maximum", "add": 60, "kind": "mixed"},
    "BETTENDORF_2103 Kimberly Road - 2026": {
        "note": "sixty-one, which must refuse", "add": 61, "kind": "mixed"},
    "CEDAR RAPIDS_1580 Blairs Ferry Road NE - 2026 Tax": {
        "note": "large phone photographs and rotated EXIF", "add": 8, "kind": "large"},
    "CLINTON_622 S 4th Street - 2025 Tax": {
        "note": "HEIC, PNG and JPEG together", "add": 8, "kind": "formats"},
    "DAVENPORT_2840 Brady Street - 2026 Tax": {
        "note": "Mark's own twelve, untouched", "add": 0, "kind": "none"},
    "DAVENPORT_7719 Northwest Boulevard - 2026": {
        "note": "portrait, landscape and small images that must not grow",
        "add": 9, "kind": "shapes"},
    "MOLINE_3400 41st Avenue Drive - Rent Study": {
        "note": "some photographs excluded from the report", "add": 10,
        "kind": "mixed", "cut": 3},
    "MUSCATINE_910 Grandview Avenue ROW": {
        "note": "captions part reviewed, part not, one edited", "add": 9,
        "kind": "mixed", "reviewed": 5, "captioned": 7},
}

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


def add_photos(photos_dir: Path, how_many: int, kind: str) -> list:
    """Add exactly this many, never overwriting anything already there."""
    photos_dir.mkdir(parents=True, exist_ok=True)
    shapes = SHAPES.get(kind, SHAPES["mixed"])
    made = []
    for i in range(how_many):
        width, height = shapes[i % len(shapes)]
        image = panel(width, height, i + 1, "demo view %02d" % (i + 1))

        suffix = ".jpg"
        if kind == "formats":
            suffix = [".jpg", ".png", ".heic"][i % 3]
        target = photos_dir / ("demo-%02d%s" % (i + 1, suffix))
        if target.exists():
            continue

        if suffix == ".png":
            image.save(target, format="PNG", optimize=True)
        elif suffix == ".heic":
            if not HEIF_READY:
                raise SystemExit(
                    "pillow-heif is not installed, so no HEIC can be written and\n"
                    "the demo would silently claim a format it does not have.\n"
                    "Install the pinned requirements and run this again.")
            image.save(target, format="HEIF", quality=70)
        elif kind == "large" and i % 3 == 1:
            # One rotated photograph per large job, recorded the way a phone
            # records it: upright pixels plus an orientation tag.
            exif = image.getexif()
            exif[0x0112] = 6
            image.save(target, format="JPEG", quality=72, exif=exif, optimize=True)
        else:
            image.save(target, format="JPEG", quality=72, optimize=True)
        made.append(target)
    return made


def write_manifest(job: Path, cut: int = 0, reviewed: int = 0, captioned: int = 0) -> None:
    """A fixture manifest, so review and exclusion states can be looked at.

    Only written when a job actually needs one of those states. Everything
    else is left with no manifest, which is the ordinary starting point.
    """
    if not (cut or reviewed or captioned):
        return
    photos_dir = job / "Photos"
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
         "caption_style": "view", "photos": entries}, indent=2), encoding="utf-8")


def hydrate(baseline: Path) -> dict:
    report = {}
    for name, spec in PLAN.items():
        job = baseline / name
        if not job.is_dir():
            report[name] = "not present, skipped"
            continue
        photos_dir = job / "Photos"
        before = len([p for p in photos_dir.iterdir()
                      if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic")]
                     ) if photos_dir.is_dir() else 0
        made = add_photos(photos_dir, spec["add"], spec["kind"]) if spec["add"] else []
        write_manifest(job, spec.get("cut", 0), spec.get("reviewed", 0),
                       spec.get("captioned", 0))
        after = len([p for p in photos_dir.iterdir()
                     if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic")])
        report[name] = "%d -> %d (%s), %s" % (before, after, len(made), spec["note"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
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
    print("  %s\n" % baseline)
    for name, line in sorted(hydrate(baseline).items()):
        print("  %-52s %s" % (name[:52], line))

    print("\n  rewriting the baseline checksums")
    demo.write_checksums(baseline, baseline.parent / demo.CHECKSUM_NAME)

    if args.reset:
        print("  restoring the working copy through Reset Demo")
        demo.reset()
        print("  done")
    return 0


if __name__ == "__main__":
    sys.exit(main())

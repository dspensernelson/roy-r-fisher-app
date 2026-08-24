"""Real photographs for demos and practice jobs, copied and sanitised.

Spenser authorised copying photographs out of `RRF/Report Examples` on
2026-08-20, for local testing and for the practice jobs inside the package.
Both the development hydration and the packaged practice jobs come through
here, so the rules are written once and cannot drift apart.

The source is strictly read-only. Files are opened for reading and nothing
else: never moved, renamed, edited, deleted, resized or rewritten.

What lands anywhere else is a sanitised copy, never the file itself:

- rebuilt from the pixels, so no EXIF and no GPS survives. Converting and
  resizing is not enough on its own, because Pillow writes `info["exif"]`
  back out for JPEG even when no exif argument is given, and the camera make
  and the capture date rode along until this was fixed.
- given a generic name, so no client filename or date travels
- carrying no document, address, caption or report content, because only
  pixels are read

If the source is not on this machine there is nothing to copy, and every
caller is expected to stop rather than quietly substitute something else. A
practice job full of placeholder panels is what this replaced.
"""
import os
from pathlib import Path

from PIL import Image, ImageOps

# The read-only source Spenser authorised.
SOURCE = Path(__file__).resolve().parents[2] / "RRF" / "Report Examples"

# Real camera photographs, by size. Below this is a logo or an icon; above it
# is usually a scan rather than a photograph.
MIN_BYTES, MAX_BYTES = 120_000, 12_000_000


class SourceUnavailable(Exception):
    """The approved photograph source is not on this machine."""


def photographs(source: Path = None) -> list:
    """Every usable photograph in the source, sorted, read-only.

    Sorted so two runs pick the same files in the same order, which is what
    makes a build reproducible.
    """
    root = Path(source) if source else SOURCE
    if not root.is_dir():
        return []
    found = []
    for dirpath, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            if not name.lower().endswith((".jpg", ".jpeg")):
                continue
            path = Path(dirpath) / name
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if not (MIN_BYTES <= size <= MAX_BYTES):
                continue
            if not _is_landscape(path):
                continue
            found.append(path)
    return found


def _is_landscape(path: Path) -> bool:
    """Wider than it is tall, once the camera's orientation is applied.

    Size alone was the only filter here, over the whole of `Report Examples`,
    so this swept up sketches, market-overview images and anything else that
    happened to be a JPEG of about the right weight. Twelve of the seventy-three
    practice photographs came out portrait.

    Not one photograph in any photo document Mark delivers is portrait: Mason
    City fifty, 217 East 37th Street twenty-four, Burlington six, all landscape.
    A practice job is meant to look like his work, and a portrait photograph in
    it is a lie about what his work contains. It cost a day: it was read as
    evidence about his reports and a fix was built on top of it.

    Orientation is applied before the comparison, because a photograph taken
    sideways is stored landscape with a flag saying otherwise, and it is the
    displayed shape that matters.
    """
    try:
        with Image.open(path) as opened:
            upright = ImageOps.exif_transpose(opened)
            width, height = upright.size
    except Exception:
        return False
    return width > height


def require(how_many: int, source: Path = None) -> list:
    """The photographs, or a clear stop. Never a silent substitute."""
    pool = photographs(source)
    if len(pool) < how_many:
        raise SourceUnavailable(
            "The approved photograph source is not available on this machine,\n"
            "so the practice jobs cannot be built with real photographs.\n"
            "\n"
            "  looked in : %s\n"
            "  found     : %d usable photographs, needed %d\n"
            "\n"
            "This is a development machine requirement, not something Mark ever\n"
            "needs. Nothing is substituted: a practice job full of placeholder\n"
            "panels is exactly what this replaced." % (SOURCE, len(pool), how_many))
    return pool


def sanitise(source: Path, target: Path, fmt: str = "JPEG",
             longest_edge: int = 2400, quality: int = 82) -> None:
    """One sanitised copy: oriented, capped, stripped, generically named.

    The source is opened read-only and closed before anything is written. It
    is never the file being saved.
    """
    with Image.open(source) as opened:
        upright = ImageOps.exif_transpose(opened)
        rgb = upright.convert("RGB")
        rgb.thumbnail((longest_edge, longest_edge))

        # Rebuilt from the pixels alone, which is what actually removes the
        # metadata. See the module docstring.
        clean = Image.new("RGB", rgb.size)
        clean.paste(rgb)

        if fmt == "PNG":
            clean.save(target, format="PNG", optimize=True)
        elif fmt == "HEIF":
            clean.save(target, format="HEIF", quality=quality)
        else:
            clean.save(target, format="JPEG", quality=quality, optimize=True)

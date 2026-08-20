"""Temporary copies of the photographs, made for the document and nothing else.

The builder used to hand `add_picture` the original file. python-docx stores
whatever bytes it is given inside the .docx and the width argument only sets
how big it is drawn, so a sixty-photo report of phone photographs produced a
document Word and email both struggled with, and every one of those photographs
was still full size inside it.

It also could not open a HEIC at all. python-docx recognises PNG, JPEG, GIF,
TIFF and BMP by signature and nothing else, so a .heic copied straight into a
Photos folder raised rather than building. Converting the document copy fixes
that as a consequence rather than as a special case.

Three rules govern everything here.

The originals are never touched. Not resized, not rotated, not recompressed,
not renamed, not moved. Every copy is written somewhere else and deleted
afterwards, whether the build succeeded or failed.

Orientation is applied before the resize. Nothing in the app did that before,
so a photograph a phone recorded sideways was embedded sideways. Applying it
changes how some pictures appear compared with earlier builds, and that
difference is a correction.

Nothing is ever enlarged. A small photograph stays its own size; the limit is
a ceiling, not a target.
"""
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

# HEIC is decoded by pillow-heif, which has to register itself with Pillow
# before Image.open will recognise one. photos.py does this too, and until now
# this module quietly depended on that having happened first. It is the module
# that converts HEIC for the document, so it registers the codec itself rather
# than relying on an import somewhere else having run.
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:                              # pragma: no cover - optional
    pass

# The settings, approved 2026-08-18. Named together so the usage history can
# record which set a run was produced under, because a change to any of them
# makes earlier cost observations incomparable.
LONGEST_EDGE = 1600
JPEG_QUALITY = 85
SETTINGS_VERSION = "1600-q85"

# Everything the app will consider a photograph. HEIC is decoded by
# pillow-heif, which registers itself with Pillow when it is installed.
READABLE = (".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff", ".bmp", ".gif")


class Workspace:
    """A folder of document copies that always cleans itself up.

    A context manager rather than a pair of calls, because the promise is that
    the copies are gone afterwards on both paths, and a `finally` somebody has
    to remember to write is not a promise.
    """

    def __init__(self, prefix: str = "rrf-doc-"):
        self.folder = Path(tempfile.mkdtemp(prefix=prefix))
        self.made = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def close(self) -> None:
        shutil.rmtree(self.folder, ignore_errors=True)

    def copy_for_document(self, source: Path) -> Path:
        """One RGB JPEG, oriented, capped, and quality 85.

        Returns a path inside this workspace. The source is opened read-only
        and closed before anything is written.
        """
        source = Path(source)
        with Image.open(source) as opened:
            # EXIF first, so the cap applies to the picture the right way up.
            # exif_transpose returns a new image and leaves the original object
            # alone; nothing is written back to the file.
            upright = ImageOps.exif_transpose(opened)
            rgb = upright.convert("RGB")

            longest = max(rgb.size)
            if longest > LONGEST_EDGE:
                scale = LONGEST_EDGE / float(longest)
                rgb = rgb.resize((max(1, int(round(rgb.width * scale))),
                                  max(1, int(round(rgb.height * scale)))),
                                 Image.LANCZOS)

            target = self.folder / ("%03d-%s.jpg" % (len(self.made), source.stem))
            # No exif argument, so the copy carries none. A document copy has
            # no business holding a camera's location.
            rgb.save(target, format="JPEG", quality=JPEG_QUALITY, optimize=True)

        self.made.append(target)
        return target


def fingerprint(folder: Path) -> dict:
    """Every file under this folder by size and sha256, for proving nothing moved.

    Used by the build path and by the tests to show that a build leaves every
    original exactly as it was.
    """
    import hashlib

    found = {}
    for path in sorted(Path(folder).rglob("*")):
        if not path.is_file():
            continue
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        found[path.name] = (path.stat().st_size, digest.hexdigest())
    return found

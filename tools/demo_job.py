"""Build the synthetic practice job that ships inside the Windows package.

Mark's package needs something to open. Without it the first thing he sees
after launching is a folder picker pointing at nothing, and the Subject
Photographs workflow cannot be tried at all until he has a real job in front of
him.

Everything here is drawn from nothing. No photograph, brief, address or folder
is copied from `Report Examples/`, `locker/`, the development `RRF Demo Jobs/`,
or any client folder, and this module reads none of those paths. The images are
flat coloured panels with their own number and the words SYNTHETIC DEMO written
across them, so nobody can mistake one for a property photograph even at a
glance.

This is a practice dataset, not the development demo system. It does not bring
back `demo.py`, `/api/demo`, Reset Demo, or the demo baseline, and the job it
creates is not marked AI safe. Section 25 of the pilot plan still governs what
may be sent anywhere: this material is local only, and nothing here asks for a
caption or touches the network.

One thing is deliberately left out. There is no HEIC image among the twelve,
because a HEIC placed directly into a Photos folder still fails Build today
(pilot plan Section 1b) and that is not fixed until Task 4. Shipping one would
hand Spenser a demo job with a broken button in it.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# Obviously invented. A real city and a real street would be the one thing
# somebody might later mistake for a client's job.
JOB_NAME = "ANYTOWN_100 Example Avenue - 2026"
CITY = "Anytown"
STREET = "100 Example Avenue"
STATE = "Iowa"

DEMO_PARENT = "Demo Jobs"

# Varied on purpose: landscape, portrait, square, wide, and small, so the
# document layout and the photo optimisation of Section 12 are exercised by
# something other than twelve identical rectangles.
PHOTOS = [
    ("01-front-elevation.jpg", 1600, 1200, (86, 110, 140), "Front elevation"),
    ("02-entry-door.jpg", 1200, 1600, (120, 96, 84), "Entry door"),
    ("03-parking-area.jpg", 1400, 1050, (92, 124, 96), "Parking area"),
    ("04-street-signage.jpg", 1050, 1400, (140, 108, 76), "Street signage"),
    ("05-roof-detail.png", 1024, 1024, (108, 108, 124), "Roof detail"),
    ("06-rear-elevation.jpg", 1920, 1080, (78, 96, 128), "Rear elevation"),
    ("07-utility-area.jpg", 800, 600, (132, 120, 92), "Utility area"),
    ("08-interior-corridor.jpg", 600, 800, (104, 92, 116), "Interior corridor"),
    ("09-loading-dock.jpg", 1600, 900, (88, 116, 116), "Loading dock"),
    ("10-stairwell.jpg", 900, 1600, (116, 100, 132), "Stairwell"),
    ("11-office-interior.png", 1280, 960, (128, 116, 104), "Office interior"),
    ("12-mechanical-room.jpg", 640, 480, (96, 104, 92), "Mechanical room"),
]


def _panel(width: int, height: int, colour, number: str, label: str) -> Image.Image:
    """One flat panel, numbered and labelled, readable at a thumbnail size."""
    image = Image.new("RGB", (width, height), colour)
    draw = ImageDraw.Draw(image)

    edge = tuple(min(255, c + 30) for c in colour)
    ink = tuple(min(255, c + 105) for c in colour)      # readable as a thumbnail
    margin = max(8, min(width, height) // 24)
    draw.rectangle([margin, margin, width - margin, height - margin],
                   outline=edge, width=max(3, min(width, height) // 90))

    # Pillow's default font is small, so the text is drawn once into a tight
    # image and scaled up. That keeps this working with no font file to ship
    # and no dependency on whatever fonts the build machine happens to have.
    #
    # The box is measured rather than estimated. A guess of six pixels per
    # character was wrong on this Pillow, whose default font is wider, and the
    # longest label ran off the edge of the smallest photograph.
    def stamp(text: str, scale: int, y_fraction: float):
        box = draw.textbbox((0, 0), text)
        pad = 2
        small = Image.new("RGB", (box[2] - box[0] + pad * 2,
                                  box[3] - box[1] + pad * 2), colour)
        ImageDraw.Draw(small).text((pad - box[0], pad - box[1]), text, fill=ink)
        grown = small.resize((small.width * scale, small.height * scale),
                             Image.NEAREST)
        room = width - 2 * margin
        if grown.width > room:
            ratio = room / grown.width
            grown = grown.resize((max(1, int(grown.width * ratio)),
                                  max(1, int(grown.height * ratio))), Image.NEAREST)
        image.paste(grown, ((width - grown.width) // 2,
                            int(height * y_fraction) - grown.height // 2))

    stamp(number, max(4, min(width, height) // 60), 0.34)
    stamp(label.upper(), max(2, min(width, height) // 150), 0.52)
    stamp("SYNTHETIC DEMO IMAGE", max(2, min(width, height) // 210), 0.64)
    stamp("NOT A REAL PROPERTY", max(2, min(width, height) // 210), 0.71)
    return image


def write_photos(photos_dir: Path) -> list:
    """The twelve images, with no EXIF and no location of any kind.

    Saved without an `exif` argument, so Pillow writes none. Nothing here ever
    opens a camera file, so there is no metadata to inherit and none to strip:
    these images have never had any.
    """
    photos_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for index, (name, width, height, colour, label) in enumerate(PHOTOS, start=1):
        image = _panel(width, height, colour, "%02d" % index, label)
        target = photos_dir / name
        if name.lower().endswith(".png"):
            image.save(target, format="PNG", optimize=True)
        else:
            image.save(target, format="JPEG", quality=70, optimize=True)
        written.append(target)
    return written


def build(parent: Path) -> Path:
    """Create `<parent>/Demo Jobs/<job>/` complete enough to open and use."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app" / "server"))
    import brief
    import jobs as jobs_module

    home = Path(parent) / DEMO_PARENT
    job = home / JOB_NAME
    for folder in jobs_module.MARK_FOLDERS:
        (job / folder).mkdir(parents=True, exist_ok=True)

    # Written by the app's own writer rather than by hand, so the brief cannot
    # drift from the shape the app reads back.
    brief.write_brief(job, {
        "Property address": "%s, %s, %s" % (STREET, CITY, STATE),
        "Property type": "Retail",
        "Engagement type": "Full appraisal",
        "Client (intended user)": "Example Bank (fictional)",
        "Intended use": "Practice dataset for testing this app",
        "Effective date of value": "2026-01-01",
        "Report due date": "2026-02-01",
        "Office file number": "DEMO-0001",
    }, sections=[])

    write_photos(job / "Photos")

    (home / "READ ME.txt").write_text(
        "Practice material\n"
        "=================\n"
        "\n"
        "Everything in this folder is invented. The job, the address, the\n"
        "client and all twelve photographs were generated by a program. There\n"
        "is no real property here and no client information of any kind.\n"
        "\n"
        "It is here so you can try the app straight away. Point the app at\n"
        "this Demo Jobs folder, open the job inside it, and use its Photos\n"
        "folder to build a Subject Photographs document.\n"
        "\n"
        "Nothing in here is sent anywhere.\n", encoding="utf-8")
    return job


if __name__ == "__main__":
    where = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    made = build(where)
    print("built %s" % made)

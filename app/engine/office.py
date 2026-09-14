"""Ask for a grid as a picture, or a Word file as a PDF, wherever you are.

**The one thing this file exists to do is stop the rest of the app knowing
which computer it is on.** A section that needs a comparable grid asks for a
picture. It never learns whether Excel was driven by AppleScript on Spenser's
Mac or by COM on Mark's PC, and it must never start caring.

The platform branch is the same shape `app/server/reveal.py` already uses: one
function answering "are we on Windows", so both paths stay readable and
testable from either machine.

Two steps, and the split between them is the point:

1. **Take the range out of the workbook.** Pure Python, no Office, identical on
   every machine. `gridextract.py` does it, and it is the reason Excel never
   opens one of Mark's files.
2. **Render the small copy.** Office, and completely different on each
   platform.

So the risky, unportable half is as small as it can be, and everything that
decides what the picture contains is in the half that runs anywhere.

**A missing Office is not a crash.** It is a sentence saying what is not there.
Photo pages need no Office at all, so a machine without it must keep working
for everything the app already does. Nothing here is imported until it is used.

Standard library plus openpyxl. The Office libraries load inside the backends,
never at import time, because importing pywin32 on a Mac is an error and
importing it on a Windows machine that lacks it must not take the app down.
"""
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import gridextract  # noqa: E402  openpyxl only, no Office


class OfficeRefused(Exception):
    """Office is not here, or it would not do it. Worded to be read."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


NO_OFFICE = (
    "This computer cannot make that, because Microsoft Excel and Word are not "
    "installed on it.\n"
    "Everything else in the app still works. Photographs need no Office at "
    "all.")


def on_windows() -> bool:
    """One function, so a Windows-only and a Mac-only path are both testable
    from either machine. Same reason as `reveal.on_windows`."""
    return sys.platform.startswith("win")


def _load_backend():
    """The module for this platform, imported now rather than at start up.

    Import errors are turned into a refusal on purpose. On a Mac `office_win`
    cannot import at all, and on a Windows machine whose package was built
    wrong it may not either, and neither is a reason for the whole app to fail
    to start.
    """
    if on_windows():
        try:
            import office_win
            return office_win
        except Exception as exc:
            raise OfficeRefused(
                "This copy of the app cannot drive Excel and Word:\n    %s\n\n"
                "Send Spenser this message." % exc)
    try:
        import office_mac
        return office_mac
    except Exception as exc:
        raise OfficeRefused(
            "This copy of the app cannot drive Excel and Word:\n    %s\n\n"
            "Send Spenser this message." % exc)


def backend(using=None):
    """The thing that will actually drive Office, or a refusal saying why not.

    `using` lets a test hand in a stand-in. Every function below takes it and
    passes it down, so nothing in this module ever reaches for a real Excel
    when a test did not ask for one.
    """
    found = using if using is not None else _load_backend()
    if not found.available():
        raise OfficeRefused(NO_OFFICE)
    return found


def describe(using=None) -> str:
    """What is going to do the work, in a sentence, for the check tool."""
    try:
        return backend(using).name()
    except OfficeRefused as exc:
        return exc.message


# ------------------------------------------------------------- the work ----
def grid_to_image(workbook, sheet, cell_range, out_png, landscape=False,
                  workshop=None, using=None) -> Path:
    """One range of one sheet, as a picture, the way Mark's paste looks.

    `workshop` is a folder to leave the working files in. Given one, nothing is
    tidied up, which is what the check tool wants when somebody is trying to
    see where a chain broke. Left out, a temporary folder is made and removed.
    """
    engine = backend(using)
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)

    keep = workshop is not None
    place = Path(workshop) if keep else Path(tempfile.mkdtemp(prefix="rrf-grid-"))
    try:
        little = gridextract.extract(workbook, sheet, cell_range, place,
                                     landscape=landscape)
        engine.render_grid(little, out_png)
    finally:
        if not keep:
            shutil.rmtree(str(place), ignore_errors=True)

    if not out_png.is_file() or out_png.stat().st_size == 0:
        raise OfficeRefused(
            "Excel was asked for a picture of %s and produced nothing.\n"
            "Nothing of yours was changed." % cell_range)
    return out_png


def docx_to_pdf(docx, out_pdf, using=None) -> Path:
    """A finished Word document as a PDF, through Mark's own Word."""
    engine = backend(using)
    docx = Path(docx)
    if not docx.is_file():
        raise OfficeRefused("There is no document at:\n    %s" % docx)
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    engine.docx_to_pdf(docx, out_pdf)

    if not out_pdf.is_file() or out_pdf.stat().st_size == 0:
        raise OfficeRefused(
            "Word was asked to make a PDF of %s and produced nothing.\n"
            "The document itself is fine and was not changed." % docx.name)
    return out_pdf

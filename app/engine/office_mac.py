"""Driving Excel and Word on a Mac, so Spenser can see real output locally.

**This side is the development convenience. The Windows side is the product.**
Mark and his office run Windows. Everything here exists so that grids and PDFs
can be looked at on the machine the app is written on, instead of every change
needing a virtual machine. If this side is a little imperfect it costs a
developer some time. If the Windows side is imperfect it reaches a client.

Adapted from the locker's `xlsm_exhibit.py` and `render_pages.py`, both proven
against Mark's delivered reports through 2026. Quarry, not a drop-in.

**How a grid becomes a picture, and why by this route.** Excel is asked to
`copy picture` with printer appearance, which puts a vector PDF of the range on
the clipboard. That is the exact artifact Mark produces when he copies a grid
and pastes it into Word, so it is the delivered look by the delivered
mechanism. The clipboard PDF is written to disk, drawn with CoreGraphics, and
cropped.

Excel's `save as` was the earlier route and Office 16.111 broke it outright, a
parameter error on every file format and every path shape. `copy picture` is
unaffected and it also skips page setup entirely, because a range copies at its
natural column widths exactly like a paste.

**Two things this does to the machine, both worth knowing.** It briefly
replaces whatever is on the clipboard. And it brings Excel to the front, so it
is not something to run while somebody is typing.

**Word and Excel have to be warm**, meaning already open and past any sign-in
dialog. A cold application answers AppleScript with error -1708 or -10006 and
the message below says so, because the fix is to click into the application and
never to quit it.

Paths are escaped before they reach AppleScript. A job folder name is arbitrary
text off Mark's own disk and can hold quotation marks, and an unescaped one
would break the script or change what it says. Same reason `reveal.py` never
lets a path reach a shell.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import office  # noqa: E402  its backend imports are inside functions, so no cycle

EXCEL_APP = Path("/Applications/Microsoft Excel.app")
WORD_APP = Path("/Applications/Microsoft Word.app")

# Long enough for a whole report. osascript's own default is 120 seconds, and a
# big document exceeds it and looks like it has hung when it is still working.
WORD_TIMEOUT = 590
EXCEL_TIMEOUT = 300

# How much bigger than its natural size the picture is drawn. 200 dots per inch
# against the PDF's 72 keeps small type readable in a report page.
RENDER_SCALE = 200.0 / 72.0

COLD_APPLICATION = (
    "\n\nIf that mentions -1708, -10006, or an object that does not "
    "understand, then Excel or Word is cold or has a dialog waiting. Click "
    "into it, close the dialog, and open and close one document. Do not quit "
    "it.")

STUCK = (
    "\n\nLook at Excel and Word on this computer. One of them may be showing "
    "a box that is waiting for you.")


def available() -> bool:
    return EXCEL_APP.is_dir() and WORD_APP.is_dir()


def name() -> str:
    return "Microsoft Excel and Word on this Mac, through AppleScript"


def _quoted(path) -> str:
    """One path, safe to drop inside an AppleScript string.

    Backslash first, or it would escape the escapes added afterwards.
    """
    text = str(path)
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _osascript(script: str, timeout: int):
    """Run one script, and turn silence into a sentence.

    Office asks a person questions and cannot tell us it is asking. On
    2026-09-04 Word sat on a Grant access box for seven minutes and said
    nothing at all, which from here looks exactly like a machine that has
    stopped. A wait with no message is the fault this app keeps fixing, so it
    is not left as a raised timeout for somebody else to catch.
    """
    try:
        return subprocess.run(["osascript", "-e", script],
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise office.OfficeRefused(
            "Office did not answer within %d minutes.%s" % (timeout // 60, STUCK))


# ----------------------------------------------------------- the picture ---
def _copy_picture_to_pdf(little: Path, pdf: Path) -> None:
    """Open the small workbook, copy its used range as a picture, save that.

    The POSIX path is turned into a file outside the `tell` block on purpose.
    Office 16.110 and later reject a slash path given straight to `open`, and
    the symptom is a dialog naming an empty file rather than an error.
    """
    import openpyxl
    across = openpyxl.load_workbook(str(little)).active.dimensions

    script = (
        'set inFile to POSIX file "%s"\n'
        'with timeout of %d seconds\n'
        '  tell application "Microsoft Excel"\n'
        '    activate\n'
        '    open inFile\n'
        '    delay 2\n'
        '    copy picture range "%s" of active sheet appearance printer '
        'format picture\n'
        '    close active workbook saving no\n'
        '  end tell\n'
        'end timeout' % (_quoted(little), EXCEL_TIMEOUT, across))

    done = _osascript(script, EXCEL_TIMEOUT + 30)
    if done.returncode != 0:
        _shut_any_stray_workbook()
        raise office.OfficeRefused(
            "Excel would not copy the grid.\n\nIt said:\n    %s%s"
            % (done.stderr.strip(), COLD_APPLICATION))

    written = _osascript(
        'set f to open for access POSIX file "%s" with write permission\n'
        'set eof f to 0\n'
        'write (the clipboard as \xabclass PDF \xbb) to f\n'
        'close access f' % _quoted(pdf), 60)
    if written.returncode != 0 or not pdf.is_file() or pdf.stat().st_size < 500:
        raise office.OfficeRefused(
            "Excel copied the grid but the picture could not be saved.\n\n"
            "It said:\n    %s" % written.stderr.strip())


def _shut_any_stray_workbook() -> None:
    """Close the small workbook if a failed attempt left it open.

    Never raises. This runs while something has already gone wrong, and a
    tidy-up that can itself fail would hide the real message.
    """
    try:
        _osascript(
            'tell application "Microsoft Excel" to close '
            '(every workbook whose name is "grid.xlsx") saving no', 30)
    except (OSError, subprocess.SubprocessError):
        pass


def _pdf_to_png(pdf: Path, png: Path, scale: float = RENDER_SCALE) -> None:
    """Draw the first page with CoreGraphics, which every Mac already has.

    No new dependency and nothing to install. Written with ctypes because the
    alternative is poppler or LibreOffice, and the stack rule is Word and Excel
    only.
    """
    import ctypes
    import ctypes.util
    from ctypes import (Structure, c_char_p, c_double, c_int, c_size_t,
                        c_uint32, c_void_p)

    quartz = ctypes.CDLL(ctypes.util.find_library("Quartz"))
    core = ctypes.CDLL(ctypes.util.find_library("CoreFoundation"))

    class Point(Structure):
        _fields_ = [("x", c_double), ("y", c_double)]

    class Size(Structure):
        _fields_ = [("w", c_double), ("h", c_double)]

    class Rect(Structure):
        _fields_ = [("origin", Point), ("size", Size)]

    core.CFStringCreateWithCString.restype = c_void_p
    core.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, c_uint32]
    core.CFURLCreateWithFileSystemPath.restype = c_void_p
    core.CFURLCreateWithFileSystemPath.argtypes = [c_void_p, c_void_p, c_int, c_int]
    quartz.CGPDFDocumentCreateWithURL.restype = c_void_p
    quartz.CGPDFDocumentCreateWithURL.argtypes = [c_void_p]
    quartz.CGPDFDocumentGetPage.restype = c_void_p
    quartz.CGPDFDocumentGetPage.argtypes = [c_void_p, c_size_t]
    quartz.CGPDFPageGetBoxRect.restype = Rect
    quartz.CGPDFPageGetBoxRect.argtypes = [c_void_p, c_int]
    quartz.CGColorSpaceCreateDeviceRGB.restype = c_void_p
    quartz.CGBitmapContextCreate.restype = c_void_p
    quartz.CGBitmapContextCreate.argtypes = [c_void_p, c_size_t, c_size_t,
                                             c_size_t, c_size_t, c_void_p, c_uint32]
    quartz.CGContextDrawPDFPage.argtypes = [c_void_p, c_void_p]
    quartz.CGContextScaleCTM.argtypes = [c_void_p, c_double, c_double]
    quartz.CGBitmapContextCreateImage.restype = c_void_p
    quartz.CGBitmapContextCreateImage.argtypes = [c_void_p]
    quartz.CGImageDestinationCreateWithURL.restype = c_void_p
    quartz.CGImageDestinationCreateWithURL.argtypes = [c_void_p, c_void_p,
                                                       c_size_t, c_void_p]
    quartz.CGImageDestinationAddImage.argtypes = [c_void_p, c_void_p, c_void_p]
    quartz.CGImageDestinationFinalize.restype = c_int
    quartz.CGImageDestinationFinalize.argtypes = [c_void_p]
    quartz.CGContextSetRGBFillColor.argtypes = [c_void_p, c_double, c_double,
                                                c_double, c_double]
    quartz.CGContextFillRect.argtypes = [c_void_p, Rect]

    def text(value):
        return core.CFStringCreateWithCString(None, value.encode(), 0x8000100)

    document = quartz.CGPDFDocumentCreateWithURL(
        core.CFURLCreateWithFileSystemPath(None, text(str(pdf)), 0, 0))
    if not document:
        raise office.OfficeRefused(
            "The picture Excel made could not be opened:\n    %s" % pdf)
    page = quartz.CGPDFDocumentGetPage(document, 1)
    box = quartz.CGPDFPageGetBoxRect(page, 0)
    wide, tall = int(box.size.w * scale), int(box.size.h * scale)

    colours = quartz.CGColorSpaceCreateDeviceRGB()
    canvas = quartz.CGBitmapContextCreate(None, wide, tall, 8, wide * 4, colours, 6)
    # Painted white first. A grid drawn on transparency picks up whatever is
    # behind it in Word, which is not what a pasted grid looks like.
    quartz.CGContextSetRGBFillColor(canvas, 1, 1, 1, 1)
    quartz.CGContextFillRect(canvas, Rect(Point(0, 0), Size(wide, tall)))
    quartz.CGContextScaleCTM(canvas, scale, scale)
    quartz.CGContextDrawPDFPage(canvas, page)

    image = quartz.CGBitmapContextCreateImage(canvas)
    destination = quartz.CGImageDestinationCreateWithURL(
        core.CFURLCreateWithFileSystemPath(None, text(str(png)), 0, 0),
        text("public.png"), 1, None)
    quartz.CGImageDestinationAddImage(destination, image, None)
    if not quartz.CGImageDestinationFinalize(destination):
        raise office.OfficeRefused("The grid could not be written as a picture.")


def _crop(png: Path, pad: int = 8) -> None:
    """Trim the white margin the page brings with it.

    Pillow is already a dependency, for photographs. If it is somehow absent
    the uncropped picture is kept rather than failing: too much white is a
    blemish and no picture at all stops a report.
    """
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return
    picture = Image.open(str(png)).convert("RGB")
    white = Image.new("RGB", picture.size, (255, 255, 255))
    box = ImageChops.difference(picture, white).getbbox()
    if not box:
        return
    box = (max(0, box[0] - pad), max(0, box[1] - pad),
           min(picture.width, box[2] + pad), min(picture.height, box[3] + pad))
    picture.crop(box).save(str(png))


def render_grid(little: Path, out_png: Path) -> None:
    """The whole chain: Excel to a clipboard picture, to a file, to a PNG."""
    little = Path(little)
    out_png = Path(out_png)
    pdf = little.parent / "grid.pdf"
    _copy_picture_to_pdf(little, pdf)
    _pdf_to_png(pdf, out_png)
    _crop(out_png)


# --------------------------------------------------------------- the pdf ---
def docx_to_pdf(docx: Path, out_pdf: Path) -> None:
    """Word's own Save As PDF, which is what makes it look like his reports.

    The document is taken from `active document` rather than from what `open`
    returns, because capturing that return value threw an intermittent error on
    this build of Word.
    """
    docx = Path(docx).resolve()
    out_pdf = Path(out_pdf).resolve()
    script = (
        'set inFile to POSIX file "%s"\n'
        'with timeout of %d seconds\n'
        '  tell application "Microsoft Word"\n'
        '    open inFile\n'
        '    delay 2\n'
        '    set theDoc to active document\n'
        '    save as theDoc file name "%s" file format format PDF\n'
        '    close theDoc saving no\n'
        '  end tell\n'
        'end timeout' % (_quoted(docx), WORD_TIMEOUT, _quoted(out_pdf)))

    done = _osascript(script, WORD_TIMEOUT + 30)
    if done.returncode != 0:
        raise office.OfficeRefused(
            "Word would not make a PDF of %s.\n\nIt said:\n    %s%s"
            % (docx.name, done.stderr.strip(), COLD_APPLICATION))
    if not out_pdf.is_file():
        raise office.OfficeRefused(
            "Word said it made the PDF and it is not there:\n    %s" % out_pdf)

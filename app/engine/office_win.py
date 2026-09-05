"""Driving Excel and Word on Windows. This is the half that reaches Mark.

**Two ways to do it, and the second exists because the first may not load.**
Decided by Spenser on 2026-09-04.

`pywin32` is a library that lets Python talk to Windows programs. It is tried
first, because when Office refuses it gives a real error with a number in it,
and somebody reading that from another building can act on it.

PowerShell is the fallback. It is part of Windows, so it needs nothing
installed. `install_windows.py` already drives Windows this way to make the
Desktop icon, and that worked on Mark's machine.

**Why the fallback is not paranoia.** The package installs libraries in a way
that never runs their setup steps. `pywin32` normally uses one to register two
system files. Without it, `import win32com` fails on Windows only, where no
test here can see it. `_wake_pywin32` below does that registration by hand, and
if it is still wrong, PowerShell carries on working.

**How a grid becomes a picture, and why by this route.** Excel copies the range
as a picture, the same command a person uses. The picture goes on the
clipboard, which Python cannot easily read on Windows. So it is pasted into an
empty chart, and the chart is exported as a PNG file.

The chart step looks odd and it earns its place. The other route is to export a
PDF and turn that into an image, and nothing in this package can turn a PDF
into an image on Windows.

**Office is started as a new, hidden copy.** Mark may have his own workbook open
while the app runs. A new copy cannot see his windows, cannot disturb them, and
is closed again afterwards.

Nothing in this file runs on a Mac. `office.py` imports it only on Windows, and
importing it anywhere is safe: every Windows-only call is inside a function.
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import office  # noqa: E402  its backend imports are inside functions, so no cycle

# Excel's own numbers for "draw it the way it would print" and "as a picture,
# not a bitmap". Written out because the names are only available once Excel is
# already talking to us, and these have to be known before that.
XL_PRINTER = 2
XL_PICTURE = -4147

# Word's number for "make a PDF".
WD_PDF = 17

# How sharp the grid picture is. Measured 2026-09-04 on the virtual machine:
# without this the picture came out 320 pixels wide where the Mac made 750, and
# it looked soft.
#
# Excel exports a chart at its own size in points, turned into pixels at 96 to
# the inch. So the only way to ask for a sharper picture is to make the chart
# bigger and stretch the copied picture to fill it. That costs nothing, because
# `CopyPicture` with XL_PICTURE gives a drawing rather than a grid of dots, and
# a drawing enlarges without going soft.
GRID_DOTS_PER_INCH = 200
SCREEN_DOTS_PER_INCH = 96.0
GRID_SCALE = GRID_DOTS_PER_INCH / SCREEN_DOTS_PER_INCH

# Long enough for a whole report, short enough that a stuck Office is reported
# while somebody is still watching. Office asks a person questions and cannot
# tell us it is asking, so a wait that never ends is a real risk.
POWERSHELL_TIMEOUT = 600

STUCK = (
    "\n\nIf nothing at all happened, look at Excel and Word on this computer. "
    "One of them may be showing a box that is waiting for you.")


# --------------------------------------------------- waking the library ----
def _library_home():
    """The folder the app's libraries live in.

    Found through a library that is certainly there rather than by guessing at
    the layout, so this works in the package and in a development checkout.
    """
    import openpyxl
    return Path(openpyxl.__file__).resolve().parent.parent


def _wake_pywin32() -> None:
    """Do by hand what `pywin32` normally does for itself when it installs.

    The package installs libraries with pip's `--target`, which copies files
    and runs nothing. So `pywin32.pth`, the file that would add these folders
    and register the two system files, is copied in and never read.

    Never raises. Failing here means `pywin32` will not import, and that is a
    fallback away from being a problem rather than a reason to stop.
    """
    try:
        home = _library_home()
    except Exception:
        return
    for part in ("win32", "win32/lib", "pythonwin"):
        folder = home / part
        if folder.is_dir() and str(folder) not in sys.path:
            sys.path.append(str(folder))
    system = home / "pywin32_system32"
    adder = getattr(os, "add_dll_directory", None)
    if system.is_dir() and adder is not None:
        try:
            adder(str(system))
        except (OSError, AttributeError):
            pass


def _com():
    """The `pywin32` way in, or None if it will not load."""
    try:
        import win32com.client
        return win32com.client
    except Exception:
        pass
    _wake_pywin32()
    try:
        import win32com.client
        return win32com.client
    except Exception:
        return None


def _powershell() -> str:
    """The PowerShell program, or an empty string when there is none."""
    import shutil
    return shutil.which("powershell") or shutil.which("pwsh") or ""


def _office_is_installed() -> bool:
    """Ask Windows whether Excel and Word are registered, without starting them.

    Reading the registry costs nothing. Starting Excel to find out whether
    Excel is there would take seconds every time the app asks.
    """
    try:
        import winreg
    except ImportError:
        return False
    for program in ("Excel.Application", "Word.Application"):
        try:
            winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, program))
        except OSError:
            return False
    return True


def available() -> bool:
    if not _office_is_installed():
        return False
    return _com() is not None or bool(_powershell())


def name() -> str:
    if _com() is not None:
        return "Microsoft Excel and Word on this PC, through pywin32"
    if _powershell():
        return "Microsoft Excel and Word on this PC, through PowerShell"
    return "nothing on this PC can drive Excel and Word"


# ------------------------------------------------------------ PowerShell ---
def _ps_text(value) -> str:
    """One value, safe inside a PowerShell single-quoted string.

    A single quote is doubled, which is the only escape a single-quoted
    PowerShell string has. Nothing else in a path can change what the script
    does, because a single-quoted string expands nothing.
    """
    return str(value).replace("'", "''")


def _run_powershell(script: str, work: Path, what: str) -> None:
    """Write the script to a file and run it.

    Written to a file rather than passed on the command line. A command line
    goes through two rounds of quoting before PowerShell sees it, and a job
    folder name off Mark's disk can hold anything.
    """
    shell = _powershell()
    if not shell:
        raise office.OfficeRefused(
            "This computer has no PowerShell, so the app cannot drive Office.")
    work.mkdir(parents=True, exist_ok=True)
    written = work / "office.ps1"
    written.write_text(script, encoding="utf-8")
    try:
        done = subprocess.run(
            [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
             "Bypass", "-File", str(written)],
            capture_output=True, text=True, timeout=POWERSHELL_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise office.OfficeRefused(
            "Office did not answer within %d minutes while it was %s.%s"
            % (POWERSHELL_TIMEOUT // 60, what, STUCK))
    except (OSError, subprocess.SubprocessError) as exc:
        raise office.OfficeRefused(
            "PowerShell would not run: %s" % exc)
    if done.returncode != 0:
        raise office.OfficeRefused(
            "Office would not finish %s.\n\nIt said:\n    %s%s"
            % (what, (done.stderr or done.stdout).strip(), STUCK))


def _ps_render_grid(little: Path, out_png: Path, across: str) -> None:
    script = (
        "$ErrorActionPreference = 'Stop'\n"
        "$excel = New-Object -ComObject Excel.Application\n"
        "$excel.Visible = $false\n"
        "$excel.DisplayAlerts = $false\n"
        "try {\n"
        "  $book = $excel.Workbooks.Open('%s', $false, $true)\n"
        "  $sheet = $book.Worksheets.Item(1)\n"
        "  $area = $sheet.Range('%s')\n"
        "  $area.CopyPicture(%d, %d)\n"
        "  $wide = $area.Width * %s\n"
        "  $tall = $area.Height * %s\n"
        "  $holder = $sheet.ChartObjects().Add(0, 0, $wide, $tall)\n"
        "  $chart = $holder.Chart\n"
        "  try { $chart.ChartArea.Format.Fill.Visible = $false } catch {}\n"
        "  try { $chart.ChartArea.Format.Line.Visible = $false } catch {}\n"
        "  $chart.Paste()\n"
        "  $picture = $chart.Shapes.Item(1)\n"
        "  $picture.LockAspectRatio = $false\n"
        "  $picture.Left = 0\n"
        "  $picture.Top = 0\n"
        "  $picture.Width = $wide\n"
        "  $picture.Height = $tall\n"
        "  $chart.Export('%s', 'PNG') | Out-Null\n"
        "  $holder.Delete()\n"
        "  $book.Close($false)\n"
        "} finally {\n"
        "  $excel.Quit()\n"
        "}\n"
        % (_ps_text(little), _ps_text(across), XL_PRINTER, XL_PICTURE,
           GRID_SCALE, GRID_SCALE, _ps_text(out_png)))
    _run_powershell(script, little.parent, "drawing the grid")


def _ps_docx_to_pdf(docx: Path, out_pdf: Path, work: Path) -> None:
    script = (
        "$ErrorActionPreference = 'Stop'\n"
        "$word = New-Object -ComObject Word.Application\n"
        "$word.Visible = $false\n"
        "$word.DisplayAlerts = 0\n"
        "try {\n"
        "  $doc = $word.Documents.Open('%s', $false, $true)\n"
        "  $doc.ExportAsFixedFormat('%s', %d)\n"
        "  $doc.Close($false)\n"
        "} finally {\n"
        "  $word.Quit()\n"
        "}\n"
        % (_ps_text(docx), _ps_text(out_pdf), WD_PDF))
    _run_powershell(script, work, "making the PDF")


# ----------------------------------------------------------- the library ---
def _com_render_grid(client, little: Path, out_png: Path, across: str) -> None:
    """A new hidden Excel, so a workbook Mark has open is never disturbed."""
    excel = client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        book = excel.Workbooks.Open(str(little), False, True)
        try:
            sheet = book.Worksheets(1)
            area = sheet.Range(across)
            area.CopyPicture(XL_PRINTER, XL_PICTURE)
            wide = area.Width * GRID_SCALE
            tall = area.Height * GRID_SCALE
            holder = sheet.ChartObjects().Add(0, 0, wide, tall)
            chart = holder.Chart
            # A chart brings its own grey panel and border. Both would frame
            # the grid, and a pasted grid has no frame around it.
            for hide in ("Fill", "Line"):
                try:
                    getattr(chart.ChartArea.Format, hide).Visible = False
                except Exception:
                    pass
            chart.Paste()
            picture = chart.Shapes(1)
            picture.LockAspectRatio = False
            picture.Left = 0
            picture.Top = 0
            picture.Width = wide
            picture.Height = tall
            chart.Export(str(out_png), "PNG")
            holder.Delete()
        finally:
            book.Close(False)
    finally:
        excel.Quit()


def _com_docx_to_pdf(client, docx: Path, out_pdf: Path) -> None:
    word = client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        document = word.Documents.Open(str(docx), False, True)
        try:
            document.ExportAsFixedFormat(str(out_pdf), WD_PDF)
        finally:
            document.Close(False)
    finally:
        word.Quit()


# ---------------------------------------------------------- what is used ---
def render_grid(little: Path, out_png: Path) -> None:
    import openpyxl
    little = Path(little)
    across = openpyxl.load_workbook(str(little)).active.dimensions

    client = _com()
    if client is not None:
        try:
            _com_render_grid(client, little, Path(out_png), across)
            return
        except Exception as exc:
            # Falling through to PowerShell rather than stopping. The library
            # loading is not the same as Office answering it, and the fallback
            # is here precisely for the difference.
            _note("pywin32 could not draw the grid", exc)
    _ps_render_grid(little, Path(out_png), across)


def docx_to_pdf(docx: Path, out_pdf: Path) -> None:
    docx = Path(docx)
    out_pdf = Path(out_pdf)
    client = _com()
    if client is not None:
        try:
            _com_docx_to_pdf(client, docx, out_pdf)
            return
        except Exception as exc:
            _note("pywin32 could not make the PDF", exc)
    _ps_docx_to_pdf(docx, out_pdf, out_pdf.parent)


def _note(what: str, exc) -> None:
    """Write the first way's failure down, so the fallback does not hide it.

    Without this a machine where `pywin32` never works looks completely normal
    and quietly costs seconds on every grid. Never raises.
    """
    try:
        sys.path.insert(0, str(HERE.parent / "server"))
        import applog
        applog.note(what, error=str(exc))
    except Exception:
        pass

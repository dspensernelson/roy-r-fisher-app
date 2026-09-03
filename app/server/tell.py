"""Saying something to the person in front of the app, with or without a window.

The app used to run from a batch file, so every message went to a black console
window that sat in front of the app for as long as it was open. Spenser's words
on 2026-09-03: *"I just want the app to open like an app."*

`pythonw.exe` ships inside the package and runs with no console at all, which
is the answer. The catch is the reason the console was there: it is where a
failure was printed. Take it away naively and a package that will not start
fails in complete silence, which is worse than the window.

So this is the piece that has to exist first. It puts a message where the
person will actually see it:

- A console, when there is one. That is the development Mac, and anybody who
  starts it from a command line on purpose.
- A dialog box, when there is not. That is Mark and Colleen, every time.

`sys.stdout is None` is how `pythonw.exe` announces itself: it has nowhere to
write, so Python hands it nothing to write to.

Standard library only, like `packaging.py` and `startup.py` beside it. This
runs before any third-party import, because the failures it exists to report
include a package whose wheels never arrived.
"""
import sys

TITLE = "Roy R. Fisher"

# What MessageBoxW wants: OK button, and an icon. 0x10 is the red cross, 0x40
# is the blue "i". Named here rather than left as numbers at the call site.
_OK = 0x0
_ERROR = 0x10
_INFO = 0x40


def has_a_console() -> bool:
    """Whether anything printed here would actually be seen."""
    return sys.stdout is not None


def _dialog(message: str, icon: int) -> bool:
    """A real Windows dialog, or False if this machine cannot show one.

    Never raises. This is the last thing standing between a failure and
    silence, so it must not be able to fail in a way that hides its own
    message.
    """
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, str(message), TITLE, _OK | icon)
        return True
    except Exception:
        return False


def say(message: str) -> None:
    """Something ordinary. Printed when there is a console, and otherwise not
    shown at all: a dialog for every routine line would be worse than silence,
    because a person would learn to click it away without reading."""
    if has_a_console():
        print(message)


def problem(message: str) -> None:
    """Something that stops the app, or that the person has to act on.

    This one is always shown. A console gets it printed; a machine with no
    console gets a dialog. If even the dialog cannot be raised, it is written
    to the log, which is the last place left.
    """
    if has_a_console():
        print(message)
        return
    if _dialog(message, _ERROR):
        return
    try:
        import applog
        applog.note("could not show a message to the user", text=message)
    except Exception:
        pass

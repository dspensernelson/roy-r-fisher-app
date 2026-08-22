"""Handing a finished document to the computer that knows how to open it.

Build writes a Word file into the job's Photos folder and used to say so in a
sentence. That is true and it is not enough: the audit watched the whole
journey end with a person leaving the app to go and find the file in Explorer
himself, which is the moment a piece of software stops feeling like one.

Two things only. Open the document, and show it in its folder. Neither happens
on its own; both are a button he presses.

The platform branch is the same shape the app already uses for drive letters:
one function answering "are we on Windows", so a Windows-only and a Mac-only
call can both be tested from either machine. No shell is involved anywhere
here. The path goes to the operating system as an argument in a list, never as
a string a shell will parse, because a job folder name is arbitrary text off
Mark's own disk and can hold quotes, ampersands and backticks.

Failing to open is not failing to build. The document is already written and
already verified by the time anything here runs, so a refusal from the
operating system says what happened and says where the file is, and never
suggests the build went wrong.
"""
import os
import subprocess
import sys
from pathlib import Path


class RevealFailed(Exception):
    """The computer would not open it, worded the way Mark should read it."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def on_windows() -> bool:
    return sys.platform.startswith("win")


def _run(command: list) -> None:
    """No shell, and never a raised exit code.

    Explorer answers with a non-zero exit code in ordinary success, so the
    return code is deliberately not read. What matters is whether the command
    could be started at all.
    """
    try:
        subprocess.run(command, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, ValueError) as exc:
        raise RevealFailed(
            "This computer would not open it. The file is saved and nothing "
            "is wrong with it. Open it from the folder yourself.") from exc


def open_document(path: Path) -> None:
    """Hand the file to whatever the computer opens .docx with."""
    path = Path(path)
    if not path.is_file():
        raise RevealFailed("That file is not there any more. Nothing was changed.")
    if on_windows():
        try:
            os.startfile(str(path))          # noqa: S606 - Windows only, no shell
        except OSError as exc:
            raise RevealFailed(
                "Windows would not open it. The file is saved and nothing is "
                "wrong with it. Open it from the folder yourself.") from exc
        return
    _run(["open", str(path)])


def show_in_folder(path: Path) -> None:
    """Open the containing folder with the file already picked out."""
    path = Path(path)
    if not path.exists():
        raise RevealFailed("That file is not there any more. Nothing was changed.")
    if on_windows():
        # One argument, comma included, which is the form Explorer expects.
        _run(["explorer", "/select,%s" % path])
        return
    _run(["open", "-R", str(path)])

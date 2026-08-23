"""The JavaScript suite, run from the Python one.

The screens are React. Until now the only thing testing them was Python reading
their source and checking that a string was present, which proves the string is
there and nothing about what happens when the button is pressed. Several of the
behaviours Spenser approved are exactly that: a control that stays off until a
count is right, a second button that appears in one state only, a run that
redraws while it works, a partial result that must not be dressed as success.

Those are tested in `app/web/src/screens/*.test.jsx`, with Vitest and Testing
Library, against real DOM. This runs them, so `pytest` still covers the whole
application and nobody has to remember a second command.

It skips rather than fails when the front end's dependencies are not installed,
the same way the corpus tests skip when the corpus is not on the machine.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[1] / "web"

needs_node = pytest.mark.skipif(
    shutil.which("npm") is None or not (WEB / "node_modules" / "vitest").is_dir(),
    reason="the front end's dependencies are not installed (cd app/web && npm ci)")


@needs_node
def test_the_screens_behave_when_they_are_actually_rendered():
    done = subprocess.run(
        ["npm", "run", "--silent", "test"],
        cwd=str(WEB), capture_output=True, text=True, timeout=600)
    if done.returncode != 0:
        # The runner's own output, unedited. A summary written here would be a
        # second place for the reason to be wrong.
        sys.stdout.write(done.stdout)
        sys.stderr.write(done.stderr)
        pytest.fail("the JavaScript UI suite failed; its output is above")

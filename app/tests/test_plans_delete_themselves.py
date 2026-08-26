"""A finished plan is not allowed to survive.

Spenser's rule, 2026-08-25: every plan destroys itself. A plan is a work list,
and a finished work list is clutter that the next session reads as current.

That rule lived in HOW-WE-WORK.md and nothing enforced it, which is the same
hole the README's test count fell through when it claimed 109 tests and there
were 335. A rule kept by whoever happens to remember it is a rule that lasts
until the first busy session. So it is a test.

What counts as finished: a plan whose task boxes are all ticked. A plan with
nothing left to do has said everything it is going to say, and whatever was
worth keeping belongs in docs/ROADMAP.md, which is the file that does not
delete itself.

This test cannot tell whether the fold-back actually happened. Nothing can.
What it can do is stop a finished plan sitting in the folder pretending to be
live work, which is the failure that matters.
"""
import re
from pathlib import Path

PLANS = Path(__file__).resolve().parents[2] / "docs" / "plans"
ROADMAP = Path(__file__).resolve().parents[2] / "docs" / "ROADMAP.md"

DONE = re.compile(r"^\s*- \[x\]", re.IGNORECASE | re.MULTILINE)
OPEN = re.compile(r"^\s*- \[ \]", re.MULTILINE)


def plans():
    return sorted(PLANS.glob("*.md")) if PLANS.is_dir() else []


def test_no_finished_plan_is_still_sitting_in_the_plans_folder():
    still_here = []
    for plan in plans():
        text = plan.read_text()
        done, open_ = len(DONE.findall(text)), len(OPEN.findall(text))
        if done and not open_:
            still_here.append("%s: %d tasks, all ticked" % (plan.name, done))
    assert not still_here, (
        "A plan with every box ticked is finished and must delete itself. Fold "
        "anything worth keeping into docs/ROADMAP.md, then `git rm` it.\n  "
        + "\n  ".join(still_here))


def test_the_roadmap_is_not_in_the_plans_folder():
    """It is the file that does not delete itself, so it must not sit among the
    files that do. It lived in docs/plans until 2026-08-26 and that was a trap
    for any session reading the folder as one kind of thing."""
    assert ROADMAP.is_file(), "docs/ROADMAP.md is where the durable record lives"
    assert not (PLANS / ROADMAP.name).exists()
    for plan in plans():
        assert "roadmap" not in plan.name.lower(), plan.name


def test_the_rule_is_written_down_where_it_governs():
    """The test enforces it. HOW-WE-WORK.md is where a person reads it, and one
    without the other is either a rule nobody applies or a failure nobody can
    explain."""
    rules = (Path(__file__).resolve().parents[2] / "HOW-WE-WORK.md").read_text()
    assert "Every plan destroys itself" in rules

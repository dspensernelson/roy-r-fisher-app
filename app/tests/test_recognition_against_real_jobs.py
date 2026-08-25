"""The job-recognition rule, measured against Mark's actual folders.

Every other test of this rule builds the folders it then recognises, which
proves the code does what the code says and nothing about his work. This one
reads his real structures: the delivered reports in `Report Examples` and the
demo jobs beside them. It is the only test of this rule that can find a false
positive or a false negative in the wild.

Strictly read-only. It lists names and asks whether a name is a directory.
It never opens a file, writes, renames, moves, or takes a checksum, and it
skips entirely when the corpus is not on the machine.

Measured 2026-08-22 across 31 real folders: no false positives and no false
negatives. The evidence behind each half of the rule is in the tests below.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import jobs  # noqa: E402
import workspace  # noqa: E402
from conftest import CORPUS  # noqa: E402

DEMO = CORPUS.parent / "RRF Demo Jobs"

needs_corpus = pytest.mark.skipif(
    not CORPUS.is_dir(),
    reason="Mark's delivered reports are private and not on this machine")
needs_demo = pytest.mark.skipif(
    not DEMO.is_dir(),
    reason="the demo jobs folder is not on this machine")


def child_folders(root: Path) -> list:
    """Names only, and only whether each is a directory."""
    return sorted(Path(e.path) for e in os.scandir(root)
                  if e.is_dir() and not e.name.startswith("."))


# Not jobs, and the app must not mistake them for jobs. Named here because
# what they are is a fact about his filing, not something code can infer.
# `Aug 2026` is a folder Spenser added to the vault to keep a new example
# apart from the delivered ones. It holds a job rather than being one, and it
# is correct for the app not to recognise it: it carries no underscore and none
# of Mark's folders. It is listed here so the guard keeps testing the rule
# rather than failing on the shape of the vault.
NOT_JOBS = {"Templates and Other", "Description of Improvement Examples 8.17.26",
            "Aug 2026"}


@needs_corpus
def test_every_delivered_report_is_recognised():
    missed = [p.name for p in child_folders(CORPUS)
              if p.name not in NOT_JOBS and not workspace.looks_like_job(p)]
    assert missed == [], "these are real jobs the app would not recognise"


@needs_corpus
def test_nothing_that_is_not_a_job_is_recognised():
    wrong = [p.name for p in child_folders(CORPUS)
             if p.name in NOT_JOBS and workspace.looks_like_job(p)]
    assert wrong == [], "these are not jobs and must not be counted as jobs"


@needs_corpus
def test_the_name_rule_earns_its_place():
    """One real delivered job carries none of Mark's eight folders.

    `DAVENPORT_Hy-Vees 2019-2022` is filed differently from the rest and is
    recognised only by its name. Without the name half of the rule, raising the
    folder threshold to four would have lost a real job of his.
    """
    by_name_only = []
    for p in child_folders(CORPUS):
        if p.name in NOT_JOBS:
            continue
        signals = sum(1 for f in jobs.MARK_FOLDERS if (p / f).is_dir())
        if signals < workspace.JOB_FOLDER_SIGNALS and workspace.looks_like_job(p):
            by_name_only.append(p.name)
    assert by_name_only, "expected at least one job recognised by name alone"


@needs_corpus
def test_the_folder_rule_earns_its_place_too():
    """And one real folder is a job by structure while its name is not.

    Mark's own folder template carries all eight folders and is named nothing
    like a job. It lives inside `Templates and Other`, which is itself not
    offered as a jobs folder, so this is recorded rather than treated as a
    fault: it is what the rule sees, and Spenser decides whether it matters.
    """
    template = CORPUS / "Templates and Other" / "Mark Folder Template"
    if not template.is_dir():
        pytest.skip("the folder template is not on this machine")
    assert not workspace.JOB_NAME.match(template.name)
    assert workspace.looks_like_job(template)


@needs_corpus
def test_the_reports_folder_would_be_accepted_as_a_jobs_folder():
    """Recorded, not asserted as desirable.

    `Report Examples` holds eleven real jobs, so the app would accept it and
    list them. That is structurally correct and it is also his immutable
    evidence. The app has no notion of a read-only folder, and whether it
    should is Spenser's decision, so this test states the fact rather than
    demanding either answer.
    """
    facts = workspace.describe(CORPUS)
    assert facts["job_count"] >= 10


@needs_demo
def test_every_demo_job_is_recognised():
    missed = [p.name for p in child_folders(DEMO) if not workspace.looks_like_job(p)]
    assert missed == []


@needs_demo
def test_one_real_job_is_never_the_jobs_folder():
    """Standing inside a job, nothing in it reads as a job."""
    for job in child_folders(DEMO)[:3]:
        assert workspace.looks_like_job(job)
        assert workspace.describe(job)["job_count"] == 0, \
            "Mark's own eight folders must never each count as a job"

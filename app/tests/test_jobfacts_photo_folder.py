"""A job remembers which folder its report photographs are in.

Mark's office keeps photographs twice: full size, and a hand-shrunk set. The
folder names vary job to job, so the app cannot work out which set is the
report. It asks him once and stores the answer here, beside the city and
address corrections, in the app's own file in his home folder and never in
one of his job folders.

The interesting half of this file is the merge. `save` used to replace a
job's whole entry with just the city and the address, so recording a folder
and then correcting a city would have silently erased the folder. Mark would
have seen his report change shape with no action from him and nothing on
screen to say why, which is the confident wrong answer this app must not
produce.
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import jobfacts  # noqa: E402


def a_job(tmp_path: Path, name: str = "DAVENPORT_1 Test Street") -> Path:
    job = tmp_path / name
    (job / "Photos").mkdir(parents=True)
    (job / "Photos" / "one.jpg").write_bytes(b"not really a photograph")
    return job


def fingerprint(folder: Path) -> dict:
    found = {}
    for path in sorted(Path(folder).rglob("*")):
        if path.is_file():
            found[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


# --- the answer itself ----------------------------------------------------
def test_a_chosen_folder_round_trips(tmp_path):
    job = a_job(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_200th-Generac Dr(Land)")
    assert jobfacts.photo_folder(job) == "Report Photos_200th-Generac Dr(Land)"


def test_a_nested_folder_round_trips(tmp_path):
    """Mason City's shape: the report photographs are two levels down."""
    job = a_job(tmp_path)
    deep = "Raw pics_Walmart Mason City 4151 4th St SW/All report photos used"
    jobfacts.save_photo_folder(job, deep)
    assert jobfacts.photo_folder(job) == deep


def test_the_top_of_photos_is_a_real_answer(tmp_path):
    """"" means he chose the top of Photos. None means he has not chosen.

    They are different answers and the app acts differently on each, so they
    must never collapse into one another.
    """
    job = a_job(tmp_path)
    assert jobfacts.photo_folder(job) is None
    jobfacts.save_photo_folder(job, "")
    assert jobfacts.photo_folder(job) == ""
    assert jobfacts.photo_folder(job) is not None


def test_forgetting_the_choice_puts_it_back_to_unasked(tmp_path):
    job = a_job(tmp_path)
    jobfacts.save_photo_folder(job, "Original")
    jobfacts.forget_photo_folder(job)
    assert jobfacts.photo_folder(job) is None


def test_a_job_nobody_has_answered_for_has_no_folder(tmp_path):
    assert jobfacts.photo_folder(a_job(tmp_path)) is None


# --- the merge, which is the defect this task exists to fix ---------------
def test_saving_a_folder_leaves_the_city_and_address_alone(tmp_path):
    job = a_job(tmp_path)
    jobfacts.save(job, "Maquoketa", "200th Ave and Generac Dr")
    jobfacts.save_photo_folder(job, "Report Photos_X")
    saved = jobfacts.for_job(job)
    assert saved[jobfacts.CITY] == "Maquoketa"
    assert saved[jobfacts.ADDRESS] == "200th Ave and Generac Dr"


def test_saving_a_city_and_address_leaves_the_folder_alone(tmp_path):
    """The one that would have bitten him. He picks his folder, corrects the
    address a week later, and the report quietly changes shape."""
    job = a_job(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    jobfacts.save(job, "Maquoketa", "200th Ave and Generac Dr")
    assert jobfacts.photo_folder(job) == "Report Photos_X"


def test_forgetting_the_folder_leaves_the_city_and_address_alone(tmp_path):
    job = a_job(tmp_path)
    jobfacts.save(job, "Maquoketa", "200th Ave")
    jobfacts.save_photo_folder(job, "Report Photos_X")
    jobfacts.forget_photo_folder(job)
    saved = jobfacts.for_job(job)
    assert saved[jobfacts.CITY] == "Maquoketa"
    assert saved[jobfacts.ADDRESS] == "200th Ave"


def test_clearing_the_city_and_address_leaves_the_folder_alone(tmp_path):
    """Blank still means no correction. It must not take the folder with it."""
    job = a_job(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    jobfacts.save(job, "Maquoketa", "200th Ave")
    jobfacts.save(job, "", "")
    assert jobfacts.for_job(job).get(jobfacts.CITY) is None
    assert jobfacts.photo_folder(job) == "Report Photos_X"


# --- one job's answer is one job's ----------------------------------------
def test_two_jobs_of_the_same_name_keep_separate_answers(tmp_path):
    """Keyed by the resolved path, the way the classification store already
    is, so a demo copy and the real job never share an answer."""
    one = a_job(tmp_path / "here")
    two = a_job(tmp_path / "there")
    jobfacts.save_photo_folder(one, "Original")
    jobfacts.save_photo_folder(two, "Minimized")
    assert jobfacts.photo_folder(one) == "Original"
    assert jobfacts.photo_folder(two) == "Minimized"


def test_another_jobs_answer_survives_this_ones(tmp_path):
    one = a_job(tmp_path / "here")
    two = a_job(tmp_path / "there")
    jobfacts.save(one, "Maquoketa", "200th Ave")
    jobfacts.save_photo_folder(two, "Original")
    assert jobfacts.for_job(one)[jobfacts.CITY] == "Maquoketa"
    assert jobfacts.photo_folder(two) == "Original"


# --- nothing of Mark's is touched -----------------------------------------
def test_nothing_is_written_inside_the_job_folder(tmp_path):
    job = a_job(tmp_path)
    before = fingerprint(job)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    jobfacts.save(job, "Maquoketa", "200th Ave")
    jobfacts.photo_folder(job)
    jobfacts.forget_photo_folder(job)
    assert fingerprint(job) == before


def test_the_answer_lives_in_the_home_folder_file(tmp_path):
    job = a_job(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    assert "Report Photos_X" in jobfacts.store_file().read_text()

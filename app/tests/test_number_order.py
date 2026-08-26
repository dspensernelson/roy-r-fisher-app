"""Numbered filenames sort the way a person reads them.

Mark's office shrinks every photograph by hand, and shrinking strips the EXIF.
The capture time is the only record of the order a shoot was walked, so once it
is gone the only surviving record is the number the helper types on the front of
the filename: `1 IMG_0559`, `2 IMG_0560`, and so on up to `12`.

Sorted as text, `10` comes before `2`. So his careful numbering produced a
report in the order 1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9. Measured on the
Maquoketa job, 2026-08-25.

This changes the fallback only. A photograph that still carries its capture
time is ordered by that time exactly as before, and the test below says so,
because the fallback is what the app uses when the photograph cannot speak for
itself and it must not start overruling one that can.
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

from photo_pages import exif_order  # noqa: E402


def plain(path: Path) -> Path:
    """A photograph with no EXIF at all, which is what a resized copy is."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (60, 45), (60, 110, 160)).save(path)
    return path


def stamped(path: Path, when: str) -> Path:
    """A photograph that still knows when it was taken."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (60, 45), (90, 60, 40))
    exif = img.getexif()
    exif[36867] = when          # DateTimeOriginal
    exif[306] = when            # DateTime
    img.save(path, exif=exif)
    return path


def order(paths):
    return [p.name for p in exif_order(paths)]


def test_the_helpers_numbering_comes_out_in_his_order(tmp_path):
    """The real case, in the real shape, from the Maquoketa job."""
    names = ["%d IMG_%04d.jpeg" % (n, 558 + n) for n in range(1, 13)]
    made = [plain(tmp_path / n) for n in names]
    assert order(made) == names


def test_ten_no_longer_sorts_before_two(tmp_path):
    made = [plain(tmp_path / n) for n in ["10 b.jpg", "2 a.jpg", "1 c.jpg"]]
    assert order(made) == ["1 c.jpg", "2 a.jpg", "10 b.jpg"]


def test_a_number_anywhere_in_the_name_is_read_as_a_number(tmp_path):
    """The camera's own numbering, which is how most of his jobs are named."""
    made = [plain(tmp_path / n) for n in
            ["IMG_9.jpg", "IMG_10.jpg", "IMG_100.jpg", "IMG_2.jpg"]]
    assert order(made) == ["IMG_2.jpg", "IMG_9.jpg", "IMG_10.jpg", "IMG_100.jpg"]


def test_names_with_no_digits_sort_as_they_always_did(tmp_path):
    made = [plain(tmp_path / n) for n in ["cherry.jpg", "apple.jpg", "Banana.jpg"]]
    assert order(made) == ["apple.jpg", "Banana.jpg", "cherry.jpg"]


def test_leading_zeros_do_not_change_the_answer(tmp_path):
    made = [plain(tmp_path / n) for n in ["007 c.jpg", "7 b.jpg", "8 a.jpg"]]
    assert order(made)[-1] == "8 a.jpg"


def test_a_very_long_run_of_digits_does_not_break_it(tmp_path):
    """A filename is arbitrary text off his disk, so nothing here may assume
    a number is small enough to be a number. Sixty digits rather than four
    hundred only because a filesystem will not hold the longer name."""
    long_one = "9" * 60 + " big.jpg"
    made = [plain(tmp_path / n) for n in [long_one, "3 small.jpg"]]
    assert order(made) == ["3 small.jpg", long_one]


# --- the capture time still wins ------------------------------------------
def test_a_photograph_that_knows_when_it_was_taken_is_ordered_by_that(tmp_path):
    """Numbering must not overrule a real capture time. Here the numbers say
    one order and the camera says the opposite, and the camera wins."""
    later = stamped(tmp_path / "1 taken second.jpg", "2026:08:01 11:20:00")
    earlier = stamped(tmp_path / "2 taken first.jpg", "2026:08:01 11:19:00")
    assert order([later, earlier]) == ["2 taken first.jpg", "1 taken second.jpg"]


def test_photographs_with_a_time_come_before_ones_without(tmp_path):
    """Unchanged behaviour, restated so the fallback change cannot move it."""
    known = stamped(tmp_path / "zzz.jpg", "2026:08:01 11:19:00")
    unknown = plain(tmp_path / "aaa.jpg")
    assert order([unknown, known]) == ["zzz.jpg", "aaa.jpg"]

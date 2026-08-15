"""The thumbnail cache is the app's own exhaust. It must never count as
arrived photos, or a job with one photo and one thumbnail reads as two."""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from readiness_scan import scan_job  # noqa: E402


def test_thumbnail_cache_never_counts_as_photos(tmp_path):
    photos = tmp_path / "Photos"
    (photos / ".rrf-thumbs").mkdir(parents=True)
    Image.new("RGB", (40, 30), (10, 80, 90)).save(photos / "IMG_5100.jpg")
    Image.new("RGB", (40, 30), (10, 80, 90)).save(
        photos / ".rrf-thumbs" / "IMG_5100.jpg.jpg")
    result = scan_job(tmp_path)
    assert result["photos"]["usable"] == 1

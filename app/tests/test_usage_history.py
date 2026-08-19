"""What a run cost, kept locally, without keeping anything about the job.

The privacy half of this file is the important half. A cost audit needs counts,
tokens and rates; it does not need to know whose building it was or what the
captions said. The byte scan at the bottom is what proves the file cannot leak
what it never learned.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import state  # noqa: E402
import usage  # noqa: E402

BUCKET = "claude-opus-5/pricing-2026-08/img-1600-q85"

# Values a real run would have in front of it, none of which may reach disk.
SECRETS = {
    "job_name": "BETTENDORF_5675 Forest - 2026",
    "address": "5675 Forest, Bettendorf, Iowa",
    "filename": "IMG_4417.HEIC",
    "caption": "View of northwest corner facing southeast",
    "prompt": "Write each caption as a view statement",
    "image_data": "/9j/4AAQSkZJRgABAQEAYABgAAD",
    "api_key": "sk-ant-api03-not-a-real-key-0000",
}

GOOD_RUN = {
    "run_id": "run-1",
    "timestamp": "2026-08-19T10:00:00",
    "model": "claude-opus-5",
    "pricing_version": "2026-08",
    "pricing_rates": {"input": 0.000015, "output": 0.000075},
    "image_settings_version": "1600-q85",
    "photos_requested": 12,
    "photos_captioned": 12,
    "photos_remaining": 0,
    "api_requests": 1,
    "status": "completed",
    "estimate": 0.60,
    "token_usage": [{"input": 18000, "output": 400, "cache_read": 0}],
    "calculated_cost": 0.30,
    "learned_rate": 0.0458,
}


@pytest.fixture(autouse=True)
def bucket():
    usage.open_bucket(BUCKET)


def test_every_approved_field_round_trips():
    usage.record_run(GOOD_RUN)
    saved = usage.runs()[0]
    for field, value in GOOD_RUN.items():
        assert saved[field] == value
    assert saved["bucket"] == BUCKET


def test_a_retry_keeps_its_parent_run_id():
    usage.record_run(GOOD_RUN)
    usage.record_run({"run_id": "run-2", "parent_run_id": "run-1",
                      "photos_requested": 3, "photos_captioned": 3,
                      "status": "completed"})
    retry = [r for r in usage.runs() if r["run_id"] == "run-2"][0]
    assert retry["parent_run_id"] == "run-1"


def test_a_cost_unavailable_run_stays_unavailable():
    """Never $0. A missing number is not a cheap number, and storing it as
    zero would drag the learned rate down exactly when evidence is weakest."""
    usage.record_run({"run_id": "run-3", "status": usage.COST_UNAVAILABLE,
                      "photos_captioned": 8})
    saved = [r for r in usage.runs() if r["run_id"] == "run-3"][0]
    assert saved["status"] == usage.COST_UNAVAILABLE
    assert "calculated_cost" not in saved


def test_prior_learning_buckets_are_kept_not_replaced():
    usage.record_run(GOOD_RUN)
    usage.open_bucket("claude-opus-5/pricing-2026-09/img-1600-q85")
    usage.record_run({"run_id": "run-9", "photos_captioned": 5})

    assert len(usage.buckets()) == 2
    assert len(usage.runs()) == 2
    assert [r["run_id"] for r in usage.runs(BUCKET)] == ["run-1"]
    assert usage.current_bucket() != BUCKET


def test_unknown_fields_never_reach_disk():
    usage.record_run({"run_id": "run-4", "photos_captioned": 2,
                      "something_invented": "nope"})
    saved = [r for r in usage.runs() if r["run_id"] == "run-4"][0]
    assert "something_invented" not in saved
    assert "something_invented" not in Path(usage.store_file()).read_text(encoding="utf-8")


@pytest.mark.parametrize("field", sorted(SECRETS))
def test_a_forbidden_field_is_refused_loudly(field):
    """Dropped silently would be safe but quiet. A caller that believed it
    could pass client content has a bug, and it should fail in its own tests."""
    with pytest.raises(ValueError):
        usage.record_run({"run_id": "run-5", field: SECRETS[field]})


def test_no_client_content_reaches_the_file():
    """The byte scan. Records a full run, then looks for every value a real
    run would have had in front of it."""
    usage.record_run(GOOD_RUN)
    usage.record_run({"run_id": "run-6", "parent_run_id": "run-1",
                      "photos_captioned": 4, "status": "partial"})

    raw = Path(usage.store_file()).read_bytes()
    for name, value in SECRETS.items():
        assert value.encode("utf-8") not in raw, name
    for fragment in (b"BETTENDORF", b".HEIC", b"sk-ant", b"View of", b"/9j/4AAQ"):
        assert fragment not in raw, fragment


def test_the_file_carries_the_current_schema():
    usage.record_run(GOOD_RUN)
    data = json.loads(Path(usage.store_file()).read_text(encoding="utf-8"))
    assert data["schema"] == state.CURRENT_SCHEMA


def test_a_run_needs_a_bucket_to_belong_to(monkeypatch):
    """Observations taken under a different model or price table are not
    comparable, so a run with nowhere to belong is refused rather than mixed."""
    monkeypatch.setenv("RRF_USAGE_FILE", str(Path(usage.store_file()).parent / "fresh.json"))
    with pytest.raises(ValueError):
        usage.record_run(GOOD_RUN)


def test_task_four_arithmetic_has_not_arrived_early():
    """Storage and validation only. Cost calculation is Task 4."""
    import ast

    tree = ast.parse(Path(usage.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported == {"os", "pathlib", "state"}, imported
    assert "anthropic" not in imported

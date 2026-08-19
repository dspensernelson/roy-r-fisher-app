"""What every AI caption run cost, kept locally so the estimate can be audited.

The app shows Mark an estimated maximum before he spends money, and that
estimate learns from what runs actually cost. A learned number nobody can check
is just a different guess, so the underlying records are kept rather than only
the running average, and each one carries the pricing table and image settings
it was produced under. Without those two, recalculating an old rate later would
silently mix observations taken under different conditions.

This module stores and validates. It does not calculate cost and it does not
know what a token is worth: Task 4 owns the arithmetic and records real runs
through `record_run`.

The privacy boundary here is a requirement, not a preference. A cost audit
needs counts, tokens and rates. It does not need to know what the photographs
were of, whose building it was, or what the captions said. A file that does not
know those things cannot leak them, so this module refuses to write them rather
than trusting every future caller to leave them out.
"""
import os
from pathlib import Path

import state

STORE_NAME = ".rrf-ai-usage.json"

# Exactly what a run record may hold. A whitelist rather than a blocklist,
# because a blocklist only stops the leaks somebody already thought of.
ALLOWED_RUN_FIELDS = (
    "run_id",              # local, ours, meaningless outside this machine
    "parent_run_id",       # set when this run is a deliberate retry
    "timestamp",
    "model",
    "pricing_version",
    "pricing_rates",
    "image_settings_version",
    "photos_requested",
    "photos_captioned",
    "photos_remaining",
    "api_requests",
    "status",              # completed, partial, failed, cost_unavailable
    "estimate",            # what he was shown before the run
    "token_usage",         # per request: input, output, applicable cache
    "calculated_cost",     # when the response carried usage
    "learned_rate",        # the rate after this run
)

# Named so a mistake is loud instead of quietly dropped. Everything not on the
# allowed list above is dropped; these additionally raise, because their
# presence means a caller believed it was allowed to pass client content in.
FORBIDDEN_RUN_FIELDS = (
    "job", "job_name", "job_path", "address", "city", "street",
    "filename", "filenames", "photo", "photos", "image", "images",
    "image_data", "caption", "captions", "prompt", "prompts",
    "api_key", "key", "client", "context",
)

RUNS_KEY = "runs"
BUCKETS_KEY = "buckets"

# A run whose response carried no usage information. Never $0: a missing number
# is not a cheap number, and treating it as zero would drag the learned rate
# down exactly when the evidence is weakest.
COST_UNAVAILABLE = "cost_unavailable"


def store_file() -> Path:
    """Home folder on both Mac and Windows. RRF_USAGE_FILE overrides, for
    tests, the same way RRF_KEY_FILE already does for the key."""
    override = os.environ.get("RRF_USAGE_FILE")
    return Path(override) if override else Path.home() / STORE_NAME


def _read() -> dict:
    return state.read_json(store_file())


def clean_run(record: dict) -> dict:
    """One run record, reduced to what it is allowed to contain.

    Raises ValueError when a caller passes something from the forbidden list,
    so the mistake surfaces in that caller's own tests rather than turning into
    a quietly wider file. Anything simply unknown is dropped without ceremony.
    """
    if not isinstance(record, dict):
        raise ValueError("a run record must be an object")
    for name in record:
        if str(name).strip().lower() in FORBIDDEN_RUN_FIELDS:
            raise ValueError("a run record may never carry %r" % name)
    return {k: v for k, v in record.items() if k in ALLOWED_RUN_FIELDS}


def runs(bucket: str = "") -> list:
    """Every run record, newest last. One bucket's worth, or all of them.

    Buckets exist because observations made under a different model, price
    table, or image size are not comparable and must never be averaged
    together. Older buckets are kept, never deleted, so an old rate stays
    inspectable after a reset.
    """
    data = _read()
    everything = data.get(RUNS_KEY, [])
    if not isinstance(everything, list):
        return []
    rows = [r for r in everything if isinstance(r, dict)]
    if not bucket:
        return rows
    return [r for r in rows if r.get("bucket") == bucket]


def buckets() -> list:
    """Every learning bucket ever opened, oldest first."""
    data = _read()
    found = data.get(BUCKETS_KEY, [])
    return [b for b in found if isinstance(b, str)] if isinstance(found, list) else []


def current_bucket() -> str:
    """The bucket runs are being recorded into, or empty before the first."""
    found = buckets()
    return found[-1] if found else ""


def open_bucket(name: str) -> None:
    """Start a fresh learning bucket. Prior buckets and their runs are kept.

    Called when the model, the published pricing, the image settings, or cache
    pricing changes. Task 4 decides when that has happened; this only records
    that it did.
    """
    name = str(name).strip()
    if not name:
        raise ValueError("a bucket name is required")
    data = _read()
    found = [b for b in data.get(BUCKETS_KEY, []) if isinstance(b, str)]
    if name not in found:
        found.append(name)
    data[BUCKETS_KEY] = found
    state.write_json(store_file(), state.without_schema(data))


def record_run(record: dict, bucket: str = "") -> dict:
    """Append one run, keeping every run already recorded.

    The stored row carries its bucket so a later recalculation cannot mix
    observations from two different pricing or image configurations.
    """
    cleaned = clean_run(record)
    data = _read()
    rows = [r for r in data.get(RUNS_KEY, []) if isinstance(r, dict)]

    chosen = str(bucket).strip() or current_bucket()
    if not chosen:
        raise ValueError("open a learning bucket before recording a run")
    known = [b for b in data.get(BUCKETS_KEY, []) if isinstance(b, str)]
    if chosen not in known:
        known.append(chosen)
    cleaned["bucket"] = chosen

    rows.append(cleaned)
    data[RUNS_KEY] = rows
    data[BUCKETS_KEY] = known
    state.write_json(store_file(), state.without_schema(data))
    return cleaned

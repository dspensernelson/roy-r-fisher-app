"""Which demo photographs may leave this machine, decided in code.

Demo jobs are hydrated from sample reports so the workflow can be tested with
real-looking material. Those photographs are real property imagery belonging to
Mark's clients, and coming out of an example report does not make them
sendable. They are useful for everything that happens on this computer and for
nothing that leaves it.

Naming cannot enforce that. The caption route sends whatever the manifest says
is included, confined to the job's own Photos folder, and it consults no folder
name, no filename, and no fixture label on the way. A convention written only
into names would be enforced by whoever happened to remember it.

Two rules carry this module.

The demo root is derived, never typed. It comes from the same validated
`.rrf-demo.json` that decides whether the reset button exists at all, through
`demo.config()`, which already refuses anything that is not exactly the
approved location and refuses any link on the way to it. There is deliberately
no function here that accepts a root, so no screen, no test helper and no
future caller can name a different folder and have it trusted.

Permission is default-deny and only ever granted live. Everything under the
validated root is Local only until a job name is explicitly allowlisted, and a
job that is renamed, moved, added, or simply unrecognised stays Local only
because it is no longer the name that was approved. The stored root can make a
job more restricted; only live validation can make one less.

This module decides. It does not enforce: wiring it into the caption endpoint,
before an Anthropic client is constructed, is Task 4's work, and until that
lands nothing consults this and the caption route is not guarded.
"""
import os
from pathlib import Path

import state

# Spenser's testing tool, and not in the package Mark receives. The import has
# to be allowed to fail for the same reason main.py's does: without the guard,
# excluding demo.py stops this module importing, which stops the server
# importing, which means the app does not start at all on his machine.
#
# Absent is a coherent answer here rather than an error. No demo system means
# no validated demo root, so nothing is demo material and nothing can be marked
# AI safe. Every job is one of Mark's own, which the demo-only policy never
# touches.
try:
    import demo
except ImportError:                                  # pragma: no cover - see test_packaged_app
    demo = None

STORE_NAME = ".rrf-demo-ai-policy.json"

ROOT_KEY = "demo_root"
ALLOWLIST_KEY = "ai_safe_jobs"

# The two sentences a refusal can carry, kept here as constants so neither can
# drift and so a test can assert the wording without matching source text.
UNREADABLE_MESSAGE = ("The demo AI safety settings could not be read. "
                      "No photos were sent. Contact Spenser.")
LOCAL_ONLY_MESSAGE = ("These photographs are demo material for local testing "
                      "only, so they were not sent. Nothing was charged.")

# The three answers. Local only and not-demo are both refusals as far as
# sending is concerned; they are separate so a message can say which it is.
AI_SAFE = "ai_safe"
LOCAL_ONLY = "local_only"
NOT_DEMO = "not_demo"


def policy_file() -> Path:
    """Home folder on both Mac and Windows. RRF_AI_POLICY_FILE overrides, for
    tests, the same way RRF_KEY_FILE already does for the key."""
    override = os.environ.get("RRF_AI_POLICY_FILE")
    return Path(override) if override else Path.home() / STORE_NAME


def _read() -> dict:
    return state.read_json(policy_file())


def validated_demo_root():
    """The approved working demo folder, or None. Derived, never supplied.

    `demo.config()` returns None for anything at all that is wrong: no config
    file, demo mode off, a path that is not exactly the approved location, a
    link anywhere on the way, a missing baseline. So None here means there is
    no trustworthy demo root, and nothing can be AI safe.
    """
    if demo is None:
        return None
    paths = demo.config()
    if not paths:
        return None
    working = paths.get("working")
    return Path(working) if working else None


def stored_root() -> str:
    """The root the policy last recorded, which may restrict but never permit.

    Kept so that a demo job stays refused even when demo validation is failing
    at this moment. Falling back to it can only ever make a job more
    restricted, because AI-safe status is checked against the live root below.
    """
    value = _read().get(ROOT_KEY, "")
    return value if isinstance(value, str) else ""


def allowlist() -> list:
    """The demo job names Spenser has explicitly approved for external AI.

    Names only, and only names beneath the demo root. Nothing about a
    production job is ever recorded here.
    """
    found = _read().get(ALLOWLIST_KEY, [])
    if not isinstance(found, list):
        return []
    return sorted({n for n in found if isinstance(n, str) and n.strip()})


def _under(job: Path, root) -> bool:
    """Is this job directly beneath that root, by resolved path.

    Resolved on both sides so a link cannot make somewhere else look like the
    demo folder, and so a job that has been moved out stops matching.
    """
    if root is None:
        return False
    try:
        return Path(job).resolve().parent == Path(root).resolve()
    except OSError:
        return False


def classify_job(job) -> str:
    """AI_SAFE, LOCAL_ONLY, or NOT_DEMO for this job folder.

    AI_SAFE requires all three at once: demo validation passing right now, the
    job sitting directly under that validated root, and its exact name being on
    the allowlist. Miss any one and the answer is LOCAL_ONLY.

    A job that is under neither the live root nor the recorded one is NOT_DEMO:
    one of Mark's real jobs, which this demo-only policy never reclassifies.
    """
    live = validated_demo_root()
    if _under(job, live):
        return AI_SAFE if Path(job).name in allowlist() else LOCAL_ONLY

    remembered = stored_root()
    if remembered and _under(job, Path(remembered)):
        # The root we were told about is not validating at the moment. That is
        # a reason to refuse, never a reason to allow.
        return LOCAL_ONLY
    return NOT_DEMO


def may_send_to_ai(job) -> bool:
    """The one question the caption route will ask, in Task 4.

    Deliberately not "is it refused": the caller must ask permission and get a
    yes, so a future code path that forgets to ask fails closed rather than
    open. Task 4 calls this before constructing an Anthropic client, and the
    boundary test in test_ai_policy.py records that requirement.
    """
    return classify_job(job) == AI_SAFE


def remember_root() -> bool:
    """Record the currently validated demo root. Returns whether there was one.

    Called by Task 6's controlled demo-preparation workflow. There is no
    variant of this that takes a path.
    """
    live = validated_demo_root()
    if live is None:
        return False
    data = _read()
    data[ROOT_KEY] = str(Path(live).resolve())
    state.write_json(policy_file(), state.without_schema(data))
    return True


def mark_ai_safe(job_name: str) -> None:
    """Approve one demo job by name for external AI use.

    Task 6 calls this, once Spenser has approved that corpus. It refuses unless
    demo validation passes right now, so an allowlist entry can never be
    created against an unvalidated root. There is no screen that reaches this
    and none is added in the pilot.
    """
    name = str(job_name).strip()
    if not name:
        raise ValueError("a demo job name is required")
    live = validated_demo_root()
    if live is None:
        raise ValueError("no validated demo root, so nothing can be marked AI safe")
    if not (Path(live) / name).is_dir():
        raise ValueError("no such job under the validated demo root")

    data = _read()
    found = [n for n in data.get(ALLOWLIST_KEY, []) if isinstance(n, str)]
    if name not in found:
        found.append(name)
    data[ALLOWLIST_KEY] = sorted(set(found))
    data[ROOT_KEY] = str(Path(live).resolve())
    state.write_json(policy_file(), state.without_schema(data))


def clear_ai_safe(job_name: str) -> None:
    """Withdraw one approval. Restricting never needs a validated root."""
    name = str(job_name).strip()
    data = _read()
    found = [n for n in data.get(ALLOWLIST_KEY, []) if isinstance(n, str)]
    data[ALLOWLIST_KEY] = sorted(n for n in found if n != name)
    state.write_json(policy_file(), state.without_schema(data))

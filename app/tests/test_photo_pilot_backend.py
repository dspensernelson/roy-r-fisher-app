"""Task 4: the ceiling, the money, the review gate, and the originals.

Everything here runs with a stand-in for the model, so the whole file costs
nothing. That is deliberate and it is the point of several of these tests: the
ceiling, the refusal at 61, and the policy refusal are all proved to happen
before a client is ever constructed, which is what makes them free to prove.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

import aipolicy  # noqa: E402
import captions  # noqa: E402
import cost  # noqa: E402
import naming  # noqa: E402
import photo_prep  # noqa: E402
import pricing  # noqa: E402
import usage as usage_store  # noqa: E402
from main import create_app  # noqa: E402

JOB = "ANYTOWN_100 Example Avenue - 2026"
USED = {"input": 20000, "output": 400, "cache_write": 0, "cache_read": 0}


def make_job(home: Path, photos: int = 12, name: str = JOB) -> Path:
    job = home / name
    (job / "Photos").mkdir(parents=True)
    for i in range(photos):
        Image.new("RGB", (800, 600), (40 + i, 90, 120)).save(
            job / "Photos" / ("p%02d.jpg" % i))
    (job / "job-brief.md").write_text(
        "# Job Brief - %s\n\n## Assignment\n\n| Field | Value |\n|---|---|\n"
        "| Property address | 100 Example Avenue, Anytown, Iowa |\n" % name,
        encoding="utf-8")
    return job


@pytest.fixture
def home(tmp_path, monkeypatch):
    place = tmp_path / "jobs"
    place.mkdir()
    monkeypatch.setenv("RRF_JOBS_HOME", str(place))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-not-a-real-key")
    return place


@pytest.fixture
def client(home):
    return TestClient(create_app(), raise_server_exceptions=False)


def stand_in(monkeypatch, usage=None, fail_after=None):
    """A model that writes captions and never touches the network."""
    calls = {"batches": 0, "sent": []}

    def fake(context, paths, style=None):
        calls["batches"] += 1
        calls["sent"].append([p.name for p in paths])
        if fail_after is not None and calls["batches"] > fail_after:
            raise captions.CaptionError("Anthropic is busy.", "rate")
        return ({p.name: "View of %s" % p.stem for p in paths},
                dict(usage if usage is not None else USED))

    monkeypatch.setattr(captions, "draft_captions", fake)
    return calls


def caption_all(client, job_name=JOB):
    return client.post("/api/jobs/%s/captions" % job_name)


def review_all(client, manifest, job_name=JOB):
    for photo in manifest["photos"]:
        client.post("/api/jobs/%s/photos/%s/reviewed" % (job_name, photo["file"]))


# --- the ceiling ------------------------------------------------------------

def test_sixty_photos_is_accepted(client, home, monkeypatch):
    make_job(home, 60)
    calls = stand_in(monkeypatch)
    assert caption_all(client).status_code == 200
    assert sum(len(b) for b in calls["sent"]) == 60


def test_sixty_one_refuses_before_anything_is_sent(client, home, monkeypatch):
    make_job(home, 61)
    calls = stand_in(monkeypatch)
    answer = caption_all(client)
    assert answer.status_code == 400
    assert "61" in answer.json()["detail"] and "60" in answer.json()["detail"]
    assert calls["batches"] == 0, "the refusal reached the model"


def test_the_estimate_endpoint_reports_the_block_without_sending(client, home, monkeypatch):
    make_job(home, 61)
    calls = stand_in(monkeypatch)
    body = client.get("/api/jobs/%s/caption-estimate" % JOB).json()
    assert body["over_ceiling"] is True
    assert body["photos_to_send"] == 61
    assert calls["batches"] == 0


# --- the money --------------------------------------------------------------

def test_the_first_run_shows_the_approved_five_cent_arithmetic(client, home, monkeypatch):
    make_job(home, 12)
    stand_in(monkeypatch)
    shown = client.get("/api/jobs/%s/caption-estimate" % JOB).json()["estimate"]
    assert shown["label"] == "Estimated maximum cost"
    assert shown["arithmetic"] == "12 x $0.0500 = $0.60"


def test_the_displayed_total_rounds_up_to_the_nearest_nickel():
    assert cost.round_up(0.54) == 0.55
    assert cost.round_up(0.60) == 0.60
    assert cost.round_up(0.5001) == 0.55


def test_a_cheaper_run_lowers_the_rate_by_the_approved_formula(client, home, monkeypatch):
    make_job(home, 12)
    stand_in(monkeypatch)
    caption_all(client)

    bucket = cost.bucket_name(captions.MODEL, photo_prep.SETTINGS_VERSION)
    spent = pricing.cost_of(captions.MODEL, USED)
    expected = (cost.PRIOR_DOLLARS + spent) / (cost.PRIOR_PHOTOS + 12)
    assert abs(cost.learned_rate(bucket) - expected) < 1e-9
    assert cost.learned_rate(bucket) < cost.STARTING_RATE


def test_a_costlier_run_raises_the_rate(client, home, monkeypatch):
    make_job(home, 2)
    stand_in(monkeypatch, usage={"input": 4_000_000, "output": 100_000})
    caption_all(client)
    bucket = cost.bucket_name(captions.MODEL, photo_prep.SETTINGS_VERSION)
    assert cost.learned_rate(bucket) > cost.STARTING_RATE


def test_measured_cost_is_reported_and_never_called_actual(client, home, monkeypatch):
    make_job(home, 12)
    stand_in(monkeypatch)
    body = caption_all(client).json()
    assert body["measured"]["label"] == "Calculated API cost from measured usage"
    assert body["measured"]["calculated_cost"] > 0
    assert body["measured"]["tokens"]["input"] > 0
    assert "actual cost" not in json.dumps(body).lower()
    assert "console" in body["measured"]["note"]


def test_missing_usage_is_unavailable_and_never_zero(client, home, monkeypatch):
    make_job(home, 4)
    stand_in(monkeypatch, usage={})
    body = caption_all(client).json()
    assert body["measured"]["label"] == "Cost unavailable"
    assert body["measured"]["calculated_cost"] is None
    assert "not zero" in body["measured"]["note"]


def test_an_unavailable_cost_never_lowers_the_learned_rate(client, home, monkeypatch):
    make_job(home, 4)
    stand_in(monkeypatch, usage={})
    caption_all(client)
    bucket = cost.bucket_name(captions.MODEL, photo_prep.SETTINGS_VERSION)
    assert cost.learned_rate(bucket) == pytest.approx(cost.STARTING_RATE)


def test_a_new_model_or_price_table_starts_a_fresh_bucket():
    one = cost.bucket_name("claude-opus-5", "1600-q85")
    assert cost.bucket_name("something-else", "1600-q85") != one
    assert cost.bucket_name("claude-opus-5", "2000-q90") != one


# --- splitting, partial failure, retry --------------------------------------

def test_one_request_when_it_fits(client, home, monkeypatch):
    make_job(home, 6)
    calls = stand_in(monkeypatch)
    caption_all(client)
    assert calls["batches"] == 1


def test_a_run_splits_only_when_size_forces_it(client, home, monkeypatch):
    make_job(home, 8)
    calls = stand_in(monkeypatch)
    monkeypatch.setattr(captions, "MAX_REQUEST_BYTES", 1)   # force one per request
    caption_all(client)
    assert calls["batches"] == 8


def test_paid_work_survives_a_failure_part_way_through(client, home, monkeypatch):
    make_job(home, 8)
    monkeypatch.setattr(captions, "MAX_REQUEST_BYTES", 1)
    stand_in(monkeypatch, fail_after=3)

    body = caption_all(client).json()
    assert body["captioned"] == 3
    assert body["partial"] is True
    assert len(body["remaining"]) == 5
    assert body["error"]

    on_disk = client.get("/api/jobs/%s/manifest" % JOB).json()
    kept = [p for p in on_disk["photos"] if p["caption"].strip()]
    assert len(kept) == 3


def test_a_retry_sends_only_what_is_left_and_never_pays_twice(client, home, monkeypatch):
    make_job(home, 8)
    monkeypatch.setattr(captions, "MAX_REQUEST_BYTES", 1)
    stand_in(monkeypatch, fail_after=3)
    first = caption_all(client).json()
    already = {p["file"] for p in
               client.get("/api/jobs/%s/manifest" % JOB).json()["photos"]
               if p["caption"].strip()}

    calls = stand_in(monkeypatch)            # the retry succeeds
    second = caption_all(client).json()

    sent = [n for batch in calls["sent"] for n in batch]
    assert set(sent) == set(first["remaining"])
    assert not (set(sent) & already), "a photo already captioned was sent again"
    assert second["remaining"] == []


def test_nothing_retries_by_itself():
    assert captions.MAX_RETRIES == 0


def test_a_failure_before_any_success_captions_nothing(client, home, monkeypatch):
    make_job(home, 5)
    stand_in(monkeypatch, fail_after=0)
    body = caption_all(client).json()
    assert body["captioned"] == 0
    assert body.get("partial") is False
    assert len(body["remaining"]) == 5


# --- review -----------------------------------------------------------------

def test_ai_captions_arrive_unreviewed(client, home, monkeypatch):
    make_job(home, 4)
    stand_in(monkeypatch)
    body = caption_all(client).json()
    assert all(not p.get("reviewed") for p in body["photos"])
    assert body["review"]["text"] == "0 of 4 reviewed"


def test_one_click_reviews_one_caption(client, home, monkeypatch):
    make_job(home, 4)
    stand_in(monkeypatch)
    caption_all(client)
    body = client.post("/api/jobs/%s/photos/p00.jpg/reviewed" % JOB).json()
    assert body["review"]["text"] == "1 of 4 reviewed"


def test_editing_a_reviewed_caption_puts_it_back(client, home, monkeypatch):
    make_job(home, 3)
    stand_in(monkeypatch)
    caption_all(client)
    manifest = client.get("/api/jobs/%s/manifest" % JOB).json()
    review_all(client, manifest)
    assert client.get("/api/jobs/%s/caption-estimate" % JOB).json()["review"]["all_reviewed"]

    manifest = client.get("/api/jobs/%s/manifest" % JOB).json()
    manifest["photos"][1]["caption"] = "Something he typed instead"
    client.put("/api/jobs/%s/manifest" % JOB, json=manifest)

    after = client.get("/api/jobs/%s/manifest" % JOB).json()
    assert after["photos"][1].get("reviewed") is not True
    assert after["photos"][0].get("reviewed") is True     # the others are untouched


def test_build_refuses_until_every_included_caption_is_reviewed(client, home, monkeypatch):
    make_job(home, 4)
    stand_in(monkeypatch)
    caption_all(client)

    blocked = client.post("/api/jobs/%s/build" % JOB)
    assert blocked.status_code == 400
    assert "0 of 4 reviewed" in blocked.json()["detail"]

    review_all(client, client.get("/api/jobs/%s/manifest" % JOB).json())
    assert client.post("/api/jobs/%s/build" % JOB).status_code == 200


def test_an_excluded_photo_needs_no_review_and_never_blocks(client, home, monkeypatch):
    make_job(home, 4)
    stand_in(monkeypatch)
    caption_all(client)
    client.post("/api/jobs/%s/photos/p03.jpg/cut" % JOB)

    manifest = client.get("/api/jobs/%s/manifest" % JOB).json()
    for photo in manifest["photos"]:
        if photo["file"] != "p03.jpg":
            client.post("/api/jobs/%s/photos/%s/reviewed" % (JOB, photo["file"]))

    assert client.post("/api/jobs/%s/build" % JOB).status_code == 200


def test_there_is_no_review_everything_route(client, home):
    make_job(home, 2)
    paths = {r.path for r in create_app().routes}
    assert not [p for p in paths if "reviewed-all" in p or "approve" in p.lower()]


# --- naming -----------------------------------------------------------------

def test_the_output_is_named_from_the_brief(client, home, monkeypatch):
    make_job(home, 3)
    stand_in(monkeypatch)
    caption_all(client)
    review_all(client, client.get("/api/jobs/%s/manifest" % JOB).json())
    created = client.post("/api/jobs/%s/build" % JOB).json()["created"]
    assert created == "Anytown_100 Example Avenue Photos (Complete).docx"


def test_a_second_build_never_overwrites_the_first(client, home, monkeypatch):
    make_job(home, 3)
    stand_in(monkeypatch)
    caption_all(client)
    review_all(client, client.get("/api/jobs/%s/manifest" % JOB).json())
    first = client.post("/api/jobs/%s/build" % JOB).json()["created"]
    second = client.post("/api/jobs/%s/build" % JOB).json()["created"]
    assert first != second
    assert (home / JOB / "Photos" / first).is_file()
    assert (home / JOB / "Photos" / second).is_file()


def test_build_refuses_rather_than_guessing_a_missing_city(client, home, monkeypatch):
    job = make_job(home, 3)
    (job / "job-brief.md").write_text(
        "# Job Brief\n\n| Field | Value |\n|---|---|\n"
        "| Property address | 100 Example Avenue |\n", encoding="utf-8")
    stand_in(monkeypatch)
    caption_all(client)
    review_all(client, client.get("/api/jobs/%s/manifest" % JOB).json())

    refused = client.post("/api/jobs/%s/build" % JOB)
    assert refused.status_code == 400
    assert "city" in refused.json()["detail"]
    # and it did not fall back to the folder name or the old default
    assert not list((job / "Photos").glob("*.docx"))


def test_his_correction_wins_and_is_stored_outside_the_job(client, home, monkeypatch):
    job = make_job(home, 3)
    before = sorted(p.name for p in job.rglob("*"))

    client.put("/api/jobs/%s/facts" % JOB,
               json={"city": "Rock Island", "address": "42 Mill Road"})
    facts = client.get("/api/jobs/%s/facts" % JOB).json()
    assert facts["city"] == "Rock Island"
    assert facts["corrected"] is True
    assert facts["filename"] == "Rock Island_42 Mill Road Photos (Complete).docx"
    assert sorted(p.name for p in job.rglob("*")) == before


@pytest.mark.parametrize("joined,city,address", [
    ("5675 Forest, Bettendorf, Iowa", "Bettendorf", "5675 Forest"),
    ("100 Example Avenue, Anytown", "Anytown", "100 Example Avenue"),
    ("Unit 4, 12 Main St, Davenport, Iowa", "Davenport", "Unit 4"),
])
def test_the_parser_handles_the_shapes_a_brief_really_has(joined, city, address):
    found = naming.parse_address(joined)
    assert found["city"] == city and found["address"] == address


def test_windows_forbidden_characters_never_reach_a_filename():
    base = naming.output_base('Any:town', 'A"B<C>D|E?F*G/H\\I')
    for bad in ':"<>|?*/\\':
        assert bad not in base


# --- the policy -------------------------------------------------------------

def test_a_production_job_is_unaffected_by_the_demo_policy(client, home, monkeypatch):
    make_job(home, 3)
    stand_in(monkeypatch)
    assert aipolicy.classify_job(home / JOB) == aipolicy.NOT_DEMO
    assert caption_all(client).status_code == 200


def test_a_local_only_job_is_refused_before_a_client_exists(client, home, monkeypatch):
    make_job(home, 3)
    calls = stand_in(monkeypatch)
    monkeypatch.setattr(aipolicy, "classify_job", lambda job: aipolicy.LOCAL_ONLY)

    refused = caption_all(client)
    assert refused.status_code == 403
    assert refused.json()["detail"] == aipolicy.LOCAL_ONLY_MESSAGE
    assert calls["batches"] == 0, "local-only photos reached the model"


def test_a_damaged_policy_says_so_and_sends_nothing(client, home, monkeypatch):
    import state
    make_job(home, 3)
    calls = stand_in(monkeypatch)

    def broken(job):
        raise state.StateUnreadable("x", "damaged")

    monkeypatch.setattr(aipolicy, "classify_job", broken)
    refused = caption_all(client)
    assert refused.status_code == 409
    assert refused.json()["detail"] == aipolicy.UNREADABLE_MESSAGE
    assert calls["batches"] == 0


# --- the document -----------------------------------------------------------

def test_the_originals_are_byte_identical_after_a_build(client, home, monkeypatch):
    job = make_job(home, 4)
    stand_in(monkeypatch)
    caption_all(client)
    review_all(client, client.get("/api/jobs/%s/manifest" % JOB).json())

    before = photo_prep.fingerprint(job / "Photos")
    client.post("/api/jobs/%s/build" % JOB)
    after = photo_prep.fingerprint(job / "Photos")
    for name, facts in before.items():
        assert after[name] == facts, name


def test_no_temporary_copy_is_left_behind(client, home, monkeypatch):
    import tempfile
    job = make_job(home, 3)
    stand_in(monkeypatch)
    caption_all(client)
    review_all(client, client.get("/api/jobs/%s/manifest" % JOB).json())

    before = set(Path(tempfile.gettempdir()).glob("rrf-doc-*"))
    client.post("/api/jobs/%s/build" % JOB)
    assert set(Path(tempfile.gettempdir()).glob("rrf-doc-*")) == before


def test_the_document_carries_the_smaller_copies(client, home, monkeypatch):
    from docx import Document
    job = make_job(home, 2)
    big = job / "Photos" / "p00.jpg"
    Image.new("RGB", (4000, 3000), (30, 60, 90)).save(big, quality=95)

    stand_in(monkeypatch)
    caption_all(client)
    review_all(client, client.get("/api/jobs/%s/manifest" % JOB).json())
    created = client.post("/api/jobs/%s/build" % JOB).json()["created"]

    document = Document(str(job / "Photos" / created))
    embedded = [r.target_part.blob for r in document.part.rels.values()
                if "image" in r.reltype]
    assert embedded
    assert max(len(b) for b in embedded) < big.stat().st_size


def test_a_heic_placed_straight_in_the_folder_now_builds(client, home, monkeypatch):
    """The live defect recorded in Section 1b. python-docx cannot embed a
    HEIC, so this raised before the document copies existed."""
    pytest.importorskip("pillow_heif")
    job = make_job(home, 2)
    heic = job / "Photos" / "p02.heic"
    Image.new("RGB", (1200, 900), (70, 90, 60)).save(heic, format="HEIF")

    stand_in(monkeypatch)
    caption_all(client)
    review_all(client, client.get("/api/jobs/%s/manifest" % JOB).json())
    built = client.post("/api/jobs/%s/build" % JOB)
    assert built.status_code == 200, built.json()
    assert heic.is_file()


def test_orientation_is_applied_before_the_resize(tmp_path):
    source = tmp_path / "sideways.jpg"
    image = Image.new("RGB", (2400, 1200), (20, 40, 60))
    exif = image.getexif()
    exif[0x0112] = 6                      # rotate 90 clockwise
    image.save(source, exif=exif)

    with photo_prep.Workspace() as bench:
        with Image.open(bench.copy_for_document(source)) as out:
            assert out.height > out.width           # turned upright
            assert max(out.size) == photo_prep.LONGEST_EDGE


def test_a_small_photograph_is_never_enlarged(tmp_path):
    source = tmp_path / "small.jpg"
    Image.new("RGB", (300, 200), (10, 10, 10)).save(source)
    with photo_prep.Workspace() as bench:
        with Image.open(bench.copy_for_document(source)) as out:
            assert out.size == (300, 200)


# --- the usage history ------------------------------------------------------

def test_a_run_is_recorded_with_counts_tokens_and_rates(client, home, monkeypatch):
    make_job(home, 5)
    stand_in(monkeypatch)
    caption_all(client)

    runs = usage_store.runs()
    assert len(runs) == 1
    row = runs[0]
    assert row["photos_captioned"] == 5
    assert row["api_requests"] == 1
    assert row["calculated_cost"] > 0
    assert row["pricing_version"] == pricing.PRICING_VERSION
    assert row["image_settings_version"] == photo_prep.SETTINGS_VERSION


def test_the_usage_file_holds_no_job_address_caption_or_key(client, home, monkeypatch):
    make_job(home, 4)
    stand_in(monkeypatch)
    caption_all(client)

    raw = Path(usage_store.store_file()).read_bytes()
    for secret in (b"ANYTOWN", b"Anytown", b"100 Example Avenue", b"View of",
                   b"sk-ant", b"p00.jpg", b".jpg"):
        assert secret not in raw, secret

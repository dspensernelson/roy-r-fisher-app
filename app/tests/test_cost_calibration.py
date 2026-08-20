"""What the paid calibration proved, pinned so it cannot quietly regress.

The real runs happened once, on 2026-08-20, against a synthetic AI-safe
corpus. What they showed is written into the numbers below: the arithmetic
that turned real token counts into a real dollar figure, and the rate the
formula produced from it.

The forced failures are stand-ins on purpose. A partial failure needs a
request to fail after another has succeeded, and buying that with real money
would be paying to watch something break.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import cost  # noqa: E402
import pricing  # noqa: E402
import usage as usage_store  # noqa: E402

# Measured on 2026-08-20, three synthetic photographs, one request.
RUN_ONE = {"input": 4192, "output": 111, "cache_write": 0, "cache_read": 0}
RUN_ONE_COST = 0.0237
RUN_ONE_PHOTOS = 3


def test_the_published_rates_are_the_ones_that_were_used():
    rates = pricing.rates_for("claude-opus-5")
    assert rates["input"] == 5.00 and rates["output"] == 25.00
    assert pricing.PRICING_VERSION == "2026-06-24"


def test_the_real_token_counts_price_to_the_figure_that_was_shown():
    """4,192 input at $5/M plus 111 output at $25/M."""
    by_hand = (4192 / 1_000_000) * 5.00 + (111 / 1_000_000) * 25.00
    assert abs(by_hand - RUN_ONE_COST) < 0.0001
    assert abs(pricing.cost_of("claude-opus-5", RUN_ONE) - RUN_ONE_COST) < 0.0001


def test_the_rate_the_first_paid_run_produced():
    """$0.047995, which is what the app recorded and what the formula says."""
    after = (cost.PRIOR_DOLLARS + RUN_ONE_COST) / (cost.PRIOR_PHOTOS + RUN_ONE_PHOTOS)
    assert abs(after - 0.047995) < 1e-5
    assert after < cost.STARTING_RATE


def test_the_estimate_was_conservative_as_the_plan_predicted():
    """The plan said five cents was very likely high and nearer two. It was
    high by about six times: three photographs cost $0.0237, not $0.15."""
    shown = cost.estimate(RUN_ONE_PHOTOS)["total"]
    assert shown == 0.15
    assert RUN_ONE_COST < shown / 5


def test_a_run_records_the_rate_it_produced_not_the_one_it_started_from(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_USAGE_FILE", str(tmp_path / "usage.json"))
    usage_store.open_bucket("b")
    after = cost.rate_including("b", RUN_ONE_COST, RUN_ONE_PHOTOS)
    assert abs(after - 0.047995) < 1e-5
    assert after != cost.STARTING_RATE


def test_an_unknown_cost_still_moves_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_USAGE_FILE", str(tmp_path / "usage.json"))
    usage_store.open_bucket("b")
    assert cost.rate_including("b", None, 12) == pytest.approx(cost.STARTING_RATE)


def test_the_second_run_was_priced_at_the_learned_rate(tmp_path, monkeypatch):
    """The estimate Mark saw for run two was 2 x $0.0480, not 2 x $0.0500.
    The learning is visible in the number he reads, not only in a file."""
    monkeypatch.setenv("RRF_USAGE_FILE", str(tmp_path / "usage.json"))
    usage_store.open_bucket("b")
    usage_store.record_run({"run_id": "r1", "photos_captioned": RUN_ONE_PHOTOS,
                            "calculated_cost": RUN_ONE_COST, "status": "completed"}, "b")
    shown = cost.estimate(2, "b")
    assert shown["rate"] == pytest.approx(0.048, abs=0.0005)
    assert shown["arithmetic"].startswith("2 x $0.048")

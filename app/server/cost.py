"""What a caption run is likely to cost, and what it turned out to cost.

Two numbers, and they are deliberately not the same kind of thing.

Before a run, Mark sees an `Estimated maximum cost`. It starts at five cents a
photograph, which is a conservative guess rather than a measurement, and it
learns from what runs actually cost. The prior is heavy on purpose: the app
behaves as though it had already seen one expensive sixty-photo run, so a
single cheap run cannot swing the number he reads before spending money.

    learned rate = ($3.00 + cumulative calculated cost)
                   / (60 + cumulative successfully captioned photos)

With no evidence that is exactly $3.00 / 60, which is five cents, so the first
run shows the figure that was approved before any of this existed. Evidence
moves it gradually, and it can move up as well as down.

After a run, he sees a `Calculated API cost from measured usage`. That is this
app's arithmetic over a published price table, not a bill, and the screen says
so. Anthropic's console remains the invoice.

A run whose response carried no usage is recorded as unavailable and never as
zero. A missing number is not a cheap number, and treating it as one would drag
the learned rate down at exactly the moment the evidence is weakest.
"""
import math

import pricing
import usage as usage_store

# The prior, approved 2026-08-19. Sixty virtual photographs at five cents.
PRIOR_PHOTOS = 60
PRIOR_DOLLARS = 3.00
STARTING_RATE = PRIOR_DOLLARS / PRIOR_PHOTOS          # $0.05

# The displayed total always rounds up to the next nickel, so the figure he
# reads is never lower than the arithmetic behind it. That is why it is called
# a maximum and not a prediction.
ROUNDING = 0.05


def bucket_name(model: str, image_settings_version: str) -> str:
    """One learning bucket per set of cost-driving conditions.

    Observations taken under a different model, price table, or image size are
    not comparable and must never be averaged together, so each combination
    gets its own bucket and a change starts a fresh one.
    """
    return "%s/%s/%s" % (model or "unknown", pricing.PRICING_VERSION,
                         image_settings_version or "unknown")


def learned_rate(bucket: str = "") -> float:
    """Dollars per photograph, from the prior plus everything measured.

    Only runs with a calculated cost count. A `cost_unavailable` run
    contributes neither its cost nor its photographs, so an unknown cost can
    never pull the rate down.
    """
    spent, photos = 0.0, 0
    for run in usage_store.runs(bucket):
        cost = run.get("calculated_cost")
        captioned = run.get("photos_captioned") or 0
        if cost is None or run.get("status") == usage_store.COST_UNAVAILABLE:
            continue
        try:
            spent += float(cost)
            photos += int(captioned)
        except (TypeError, ValueError):
            continue
    return (PRIOR_DOLLARS + spent) / float(PRIOR_PHOTOS + photos)


def rate_including(bucket: str, extra_cost, extra_photos: int) -> float:
    """The learned rate once one more run is counted, before it is stored.

    A run records the rate it produced, not the rate it started from, so the
    history reads as a series of answers rather than a series of guesses. The
    record cannot be read back for this because it is still being built.

    A run with no calculated cost adds nothing, the same as everywhere else:
    an unknown cost never moves the rate.
    """
    spent, photos = 0.0, 0
    for run in usage_store.runs(bucket):
        cost_of_run = run.get("calculated_cost")
        if cost_of_run is None or run.get("status") == usage_store.COST_UNAVAILABLE:
            continue
        try:
            spent += float(cost_of_run)
            photos += int(run.get("photos_captioned") or 0)
        except (TypeError, ValueError):
            continue
    if extra_cost is not None:
        spent += float(extra_cost)
        photos += int(extra_photos or 0)
    return (PRIOR_DOLLARS + spent) / float(PRIOR_PHOTOS + photos)


def round_up(amount: float) -> float:
    """Up to the next five cents. Never down."""
    return round(math.ceil((amount - 1e-9) / ROUNDING) * ROUNDING, 2)


def estimate(photo_count: int, bucket: str = "") -> dict:
    """What the screen shows before a run, with its arithmetic.

    The rate is carried at four decimal places because that is what the
    arithmetic actually used, and showing `12 x $0.05 = $0.55` would look like
    a mistake. The total is the rounded one.
    """
    count = max(0, int(photo_count))
    rate = learned_rate(bucket)
    raw = rate * count
    return {
        "label": "Estimated maximum cost",
        "photos": count,
        "rate": round(rate, 4),
        "raw_total": round(raw, 4),
        "total": round_up(raw),
        "arithmetic": "%d x $%.4f = $%.2f" % (count, round(rate, 4), round_up(raw)),
        "is_estimate": True,
    }


def measured(model: str, usages: list) -> dict:
    """What the screen shows after a run, from what the provider reported.

    `usages` is one entry per request, because a run that had to be split made
    more than one and the whole run is reported as one figure.
    """
    totals = {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}
    priced, unavailable = 0.0, False

    for one in usages or []:
        for field in totals:
            totals[field] += int((one or {}).get(field) or 0)
        cost = pricing.cost_of(model, one or {})
        if cost is None:
            unavailable = True
        else:
            priced += cost

    if not usages or unavailable:
        return {
            "label": "Cost unavailable",
            "tokens": totals,
            "calculated_cost": None,
            "pricing_version": pricing.PRICING_VERSION,
            "note": ("The provider did not report what this run used, so the "
                     "cost cannot be calculated. It is not zero."),
        }
    return {
        "label": "Calculated API cost from measured usage",
        "tokens": totals,
        "calculated_cost": round(priced, 4),
        "pricing_version": pricing.PRICING_VERSION,
        "note": ("This app's arithmetic over published prices, not a bill. "
                 "Anthropic's console is the invoice."),
    }

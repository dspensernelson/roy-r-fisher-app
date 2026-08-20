"""What a thousand tokens costs, so measured usage can become a dollar figure.

A price table in the app goes stale when the provider changes its prices, and
a stale table would quietly report a wrong number as though it were measured.
So the table carries a version, every run records the version it was priced
under, and a model that is not in the table produces no dollar figure at all
rather than a guess.

That is the whole reason `cost_unavailable` exists. A missing price is not a
zero price.
"""

# The date this table was taken from Anthropic's published pricing. Recorded on
# every run in the usage history, so an old rate can be recalculated later
# against the prices it was actually produced under.
PRICING_VERSION = "2026-06-24"

# Dollars per million tokens.
RATES = {
    "claude-opus-5": {"input": 5.00, "output": 25.00,
                      "cache_write": 6.25, "cache_read": 0.50},
}

PER_MILLION = 1_000_000.0


def rates_for(model: str):
    """The rates for this model, or None when we do not know them.

    None is the honest answer for a model somebody has switched to without
    updating this file, and every caller turns it into `Cost unavailable`.
    """
    return RATES.get((model or "").strip())


def known(model: str) -> bool:
    return rates_for(model) is not None


def cost_of(model: str, usage: dict):
    """Dollars for one measured response, or None.

    `usage` is what the provider reported: input tokens, output tokens, and
    the cache counters when they are present. Anything missing counts as zero
    of that kind, which is different from the whole figure being unavailable:
    a response that reported no cache read really did read no cache.
    """
    rates = rates_for(model)
    if rates is None or not isinstance(usage, dict):
        return None
    if usage.get("input") is None or usage.get("output") is None:
        # The two that must be there. Without them there is nothing to price.
        return None

    total = 0.0
    for field, rate in (("input", rates["input"]), ("output", rates["output"]),
                        ("cache_write", rates.get("cache_write", 0.0)),
                        ("cache_read", rates.get("cache_read", 0.0))):
        count = usage.get(field) or 0
        try:
            total += (float(count) / PER_MILLION) * float(rate)
        except (TypeError, ValueError):
            return None
    return round(total, 6)

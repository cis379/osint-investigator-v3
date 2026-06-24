"""Canonical estimative-confidence vocabulary for the investigation graph.

The supervisor grades every finding with one of three ESTIMATIVE tiers (strongest
to weakest). These are likelihood *judgments the supervisor assigns* — never the raw
self-stamp a collection tool returns. Collection tools over-claim (several stamp every
hit "confirmed" in code); the supervisor ignores those tags and re-grades from the
evidence. The tiers:

    highly_likely  - strongest. Corroborated by INDEPENDENT evidence, or an
                     authoritative/unambiguous source. (Was labelled "confirmed".)
    probable       - likely, but single-source or inferred (not cross-checked).
    possible       - weak / candidate / likely-noise, KEPT as a pivot, not hidden.

Why "highly_likely" and not "confirmed": in OSINT almost nothing is truly confirmed —
these are analytic likelihood estimates (cf. words of estimative probability). The old
label "confirmed" read as certainty and invited over-claiming. The MECHANISM is
unchanged: three tiers, supervisor re-grades, weak hits are tiered (never dropped).

`confirmed` remains accepted as a LEGACY ALIAS for `highly_likely` so investigations
graphed before the rename keep loading and rendering. New commits use the canonical
keys above.
"""

# strongest -> weakest
CANONICAL_TIERS = ("highly_likely", "probable", "possible")

# legacy / loose spellings -> canonical key
_ALIASES = {
    "confirmed": "highly_likely",
    "highly likely": "highly_likely",
    "highly-likely": "highly_likely",
}

_HUMAN = {
    "highly_likely": "Highly likely",
    "probable": "Probable",
    "possible": "Possible",
}

# strongest (0) -> weakest (2); used for sorting and confidence-gating
TIER_RANK = {"highly_likely": 0, "probable": 1, "possible": 2}


def normalize(conf, default: str = "possible") -> str:
    """Map any incoming confidence string to a canonical tier.

    Unknown / empty values fall back to ``default``. Pass ``default=""`` when the
    caller wants to detect an unrecognised value (returns "").
    """
    if not conf:
        return default
    c = str(conf).strip().lower().replace(" ", "_").replace("-", "_")
    c = _ALIASES.get(c, c)
    return c if c in CANONICAL_TIERS else default


def humanize(conf, default: str = "highly_likely") -> str:
    """Display label for a tier, e.g. 'highly_likely' -> 'Highly likely'."""
    return _HUMAN.get(normalize(conf, default), _HUMAN[default])

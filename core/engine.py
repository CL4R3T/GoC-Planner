"""Core computation engine.

All rarity comparisons use exact integer cross-multiplication against
Fraction thresholds — no floating point in the hot path (fixes the old
float-boundary bug where large n shifted the x boundary by one).
"""

from fractions import Fraction

from core.events import Events
from generators.base import Formula


def _le_threshold(count: int, denom: int, threshold: Fraction) -> bool:
    """count / denom <= threshold  <=>  count * den_t <= num_t * denom."""
    return count * threshold.denominator <= threshold.numerator * denom


def _in_interval(count: int, denom: int, p_lower: Fraction, p_upper: Fraction) -> bool:
    """p_lower < count / denom <= p_upper, via integer cross-multiplication."""
    if not _le_threshold(count, denom, p_upper):
        return False
    # count / denom > p_lower  <=>  count * den_l > num_l * denom
    return count * p_lower.denominator > p_lower.numerator * denom


def _first_x_le(f: Formula, n: int, denom: int, threshold: Fraction) -> int | None:
    """Find the first x in valid_x(n) where f.compute(n,x)/denom <= threshold.

    Returns None if no such x exists.
    """
    for x in f.valid_x(n):
        if _le_threshold(f.compute(n, x), denom, threshold):
            return x
    return None


def _count_in_interval(
    f: Formula,
    n: int,
    denom: int,
    p_upper: Fraction,
    p_lower: Fraction,
) -> int:
    """Return number of outcomes for which formula f yields a rarity in (p_lower, p_upper].

    cumulative: boundary telescoping (nested events).
    exact: sum over individual x values (mutually exclusive events).
    binary: single boolean property per outcome (no x parameter).
    """
    if f.kind == "cumulative":
        x_low = _first_x_le(f, n, denom, p_upper)
        if x_low is None:
            return 0
        x_high = _first_x_le(f, n, denom, p_lower)
        count_low = f.compute(n, x_low)
        count_high = f.compute(n, x_high) if x_high is not None else 0
        return count_low - count_high

    elif f.kind == "exact":
        total = 0
        for x in f.valid_x(n):
            count = f.compute(n, x)
            if count == 0:
                continue
            if _in_interval(count, denom, p_lower, p_upper):
                total += count
        return total

    else:  # binary
        count = f.compute(n, 0)  # x is a dummy placeholder
        if count <= 0:
            return 0
        return count if _in_interval(count, denom, p_lower, p_upper) else 0


def prob_event(
    n: int,
    k_gen: int,
    formulas: list[Formula],
    events: Events,
    target_event: int,
) -> float:
    """Probability that at least one formula triggers target_event (1-indexed).

    Uses the independence approximation across formulas (1 - prod(1 - p_f)).
    NOTE: this approximation is wrong for correlated formulas on the same
    trial sequence; fixing it (true joint distribution) is deferred to a
    later branch. Computation itself is exact-rational here.
    """
    denom = k_gen**n
    p_upper, p_lower = events.interval_bounds(target_event)
    prob_no = Fraction(1)

    for f in formulas:
        count = _count_in_interval(f, n, denom, p_upper, p_lower)
        if count <= 0:
            continue
        p_f = Fraction(count, denom)
        prob_no *= 1 - p_f

    return float(1 - prob_no)


def find_best_n(
    n_max: int,
    k_gen: int,
    formulas: list[Formula],
    events: Events,
    target_event: int,
) -> int:
    """Return n (1 <= n <= n_max) that maximizes trigger probability of target_event."""
    best_n = 1
    best_prob = -1.0
    for n in range(1, n_max + 1):
        prob = prob_event(n, k_gen, formulas, events, target_event)
        if prob > best_prob:
            best_prob = prob
            best_n = n
    return best_n


def full_distribution(
    n: int,
    k_gen: int,
    formulas: list[Formula],
    events: Events,
) -> list[float]:
    """Return trigger probability for every event tier at given n.

    Returns:
        probs: probs[k-1] = P(event k triggers), 1-indexed
    """
    denom = k_gen**n
    m = len(events)
    probs_no = [Fraction(1)] * m

    for f in formulas:
        for k in range(1, m + 1):
            p_upper, p_lower = events.interval_bounds(k)
            count = _count_in_interval(f, n, denom, p_upper, p_lower)
            if count <= 0:
                continue
            p_f = Fraction(count, denom)
            probs_no[k - 1] *= 1 - p_f

    return [float(1 - pn) for pn in probs_no]

"""Display-side statistics shared by the CLI and web backend."""

import math


def expected_attempts(p: float) -> float:
    """Expected attempts until first success (geometric distribution)."""
    return 1.0 / p if p > 0 else float("inf")


def pity99(p: float) -> int | float:
    """Attempts needed for >= 99% chance of at least one success."""
    if p <= 0:
        return float("inf")
    if p >= 0.99:
        return 1
    return math.ceil(math.log(0.01) / math.log(1.0 - p))

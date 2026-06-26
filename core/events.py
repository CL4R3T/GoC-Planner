"""Event threshold management."""


class Events:
    """Event threshold manager.

    Attributes:
        thresholds: descending thresholds p₁ > p₂ > ... > pₘ
    """

    def __init__(self, thresholds: list[float]):
        self.thresholds = sorted(thresholds, reverse=True)

    def __len__(self) -> int:
        return len(self.thresholds)

    @property
    def p(self) -> list[float]:
        """Threshold list, p[k] = p_k (0-indexed)."""
        return self.thresholds

    def find_interval(self, rarity: float) -> int | None:
        """Return event index (1-indexed), or None if rarity is too large.

        Event k corresponds to interval (p_{k+1}, p_k].
        p_0 treated as +inf, p_{m+1} treated as 0.
        """
        if rarity > self.thresholds[0]:
            return None
        for i, t in enumerate(self.thresholds):
            if rarity > t:
                return i  # in (thresholds[i], thresholds[i-1]], i.e. event i
        return len(self.thresholds)  # <= p_m, i.e. event m

    def interval_bounds(self, k: int) -> tuple[float, float]:
        """Return interval bounds (p_upper, p_lower] for event k (1-indexed).

        p_upper = p_k (inclusive upper bound)
        p_lower = p_{k+1} (exclusive lower bound), 0 if k = m
        """
        p_upper = self.thresholds[k - 1]
        p_lower = self.thresholds[k] if k < len(self.thresholds) else 0.0
        return p_upper, p_lower

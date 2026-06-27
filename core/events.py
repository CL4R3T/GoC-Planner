"""Event threshold management with exact rational thresholds."""

from dataclasses import dataclass
from fractions import Fraction


@dataclass
class Tier:
    """A single ladder tier: name, rarity grade, and exact threshold.

    Bundling name/grade/threshold into one object guarantees they stay
    aligned through any reordering (fixes the old sort-desync bug).
    """
    name: str
    grade: str
    threshold: Fraction
    raw: str  # original prob string from config, for faithful display


class Events:
    """Event threshold manager.

    tiers: descending by threshold (p₁ > p₂ > ... > pₘ). Each tier bundles
    its display name and rarity grade alongside its threshold.
    """

    def __init__(self, tiers: list[Tier]):
        self.tiers = sorted(tiers, key=lambda t: t.threshold, reverse=True)

    def __len__(self) -> int:
        return len(self.tiers)

    @property
    def thresholds(self) -> list[Fraction]:
        """Threshold list, p[k] = p_k (0-indexed)."""
        return [t.threshold for t in self.tiers]

    def interval_bounds(self, k: int) -> tuple[Fraction, Fraction]:
        """Return interval bounds (p_upper, p_lower] for event k (1-indexed).

        p_upper = p_k (inclusive upper bound)
        p_lower = p_{k+1} (exclusive lower bound), 0 if k = m
        """
        p_upper = self.tiers[k - 1].threshold
        p_lower = self.tiers[k].threshold if k < len(self.tiers) else Fraction(0)
        return p_upper, p_lower

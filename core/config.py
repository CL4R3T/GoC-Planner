"""DEPRECATED: superseded by goc_python (Rust Ladder). Frozen; do not extend.
Removed in chunk 3 once app/main are rewired. Ladder config loader — single
source of truth for tier definitions.
"""

import os
import tomllib
from fractions import Fraction

from core.events import Events, Tier

# Expected counts per grade; load_ladder validates these.
GRADE_ORDER = ["blue", "purple", "golden", "diamond", "legendary", "impossible"]
GRADE_COUNTS = {
    "blue": 20,
    "purple": 8,
    "golden": 7,
    "diamond": 5,
    "legendary": 4,
    "impossible": 2,
}

# Grade -> display color (GitHub-dark-ish palette matching index.html).
GRADE_COLORS = {
    "blue": "#58a6ff",
    "purple": "#bc8cff",
    "golden": "#e3b341",
    "diamond": "#56d4dd",
    "legendary": "#ffa657",
    "impossible": "#f85149",
}


def parse_prob(raw: str | int | float) -> Fraction:
    """Parse a probability value into an exact Fraction.

    Supports:
      - "M/N"  -> Fraction(M, N)
      - "P%"   -> Fraction(P) / 100   (P may be a decimal like "0.024")
      - "P.Q"  -> Fraction("P.Q")
      - int/float -> Fraction(value)
    """
    if isinstance(raw, (int, float)):
        return Fraction(raw)

    s = raw.strip().replace(",", "")
    if s.endswith("%"):
        return Fraction(s[:-1]) / 100
    if "/" in s:
        num, den = s.split("/", 1)
        return Fraction(int(num), int(den))
    return Fraction(s)


def _clean_name(desc: str) -> str:
    """Strip the leading "... " stylistic prefix the game uses."""
    return desc.removeprefix("...").strip()


def load_ladder(path: str | None = None) -> Events:
    """Load ladder.toml and return an Events (tiers sorted descending).

    Each tier carries its cleaned name, grade, and exact Fraction threshold.
    """
    if path is None:
        path = os.path.join(os.path.dirname(__file__), os.pardir, "ladder.toml")
        path = os.path.normpath(path)

    with open(path, "rb") as f:
        data = tomllib.load(f)

    tiers: list[Tier] = []
    grade_seen: dict[str, int] = {g: 0 for g in GRADE_ORDER}

    for entry in data["events"]:
        grade = entry["grade"]
        if grade not in grade_seen:
            raise ValueError(f"unknown grade {grade!r} in ladder.toml")
        grade_seen[grade] += 1
        tiers.append(
            Tier(
                name=_clean_name(entry["desc"]),
                grade=grade,
                threshold=parse_prob(entry["prob"]),
                raw=entry["prob"],
            )
        )

    # Validate grade counts.
    for grade, expected in GRADE_COUNTS.items():
        if grade_seen[grade] != expected:
            raise ValueError(f"grade {grade!r} count {grade_seen[grade]} != expected {expected}")

    return Events(tiers)

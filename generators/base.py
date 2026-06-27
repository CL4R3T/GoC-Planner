"""Formula data structure."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

FormulaKind = Literal["cumulative", "exact", "binary"]


@dataclass
class Formula:
    """A feature formula.

    Attributes:
        name: formula name, e.g. "At Least X Heads"
        kind: "cumulative" (at-least, events are nested) or "exact" (exactly-x, events are mutually exclusive)
        valid_x: given n, returns sorted list of all valid x values
        compute: given (n, x), returns favorable outcome count (numerator), denominator = k**n
    """

    name: str
    kind: FormulaKind
    valid_x: Callable[[int], list[int]]
    compute: Callable[[int, int], int]

"""Event Optimizer — interactive CLI."""

import json
import math
import os

from core.engine import find_best_n, prob_event
from core.events import Events
from generators import ALL as all_generators


def _parse_prob(value) -> float:
    """Parse probability: float or '1/N' string."""
    if isinstance(value, (int, float)):
        return float(value)
    # "1/10,000" or "1/10000"
    s = value.replace(",", "")
    if s.startswith("1/"):
        return 1.0 / int(s[2:])
    return float(s)


def load_events(path: str | None = None) -> tuple[Events, list[str], list]:
    """Load event config from JSON.

    JSON format: [{"name": "...", "probability": <float> or "1/N"}, ...]
    Ordered from largest to smallest probability.
    Returns (Events, names, raw_probabilities) — raw_probabilities preserves original format for display.
    """
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "events.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    names = [entry["name"] for entry in data]
    raw_probs = [entry["probability"] for entry in data]
    thresholds = [_parse_prob(p) for p in raw_probs]
    return Events(thresholds), names, raw_probs


def load_generator(index: int):
    """Return (module_name, K, FORMULAS) for the generator at the given index."""
    mod = all_generators[index]
    name = mod.__name__.split(".")[-1]
    return name, mod.K, mod.FORMULAS


def main():
    print("=" * 50)
    print("  Event Optimizer")
    print("=" * 50)

    # 1. Select generator
    print("\nAvailable generators:")
    for i, mod in enumerate(all_generators, 1):
        name = mod.__name__.split(".")[-1]
        print(f"  [{i}] {name}")
    choice = int(input(f"\nSelect (1-{len(all_generators)}): ")) - 1
    gen_name, k_gen, all_formulas = load_generator(choice)

    # 2. Formula list
    print(f"\nFormulas (unlock order, {len(all_formulas)} total):")
    for i, f in enumerate(all_formulas, 1):
        print(f"  [{i}] {f.name}")
    if len(all_formulas) == 0:
        print("  (No formulas yet. Add them in generators/coin.py)")
        return
    f_count = int(input(f"\nUnlocked formula count (1-{len(all_formulas)}): "))
    formulas = all_formulas[:f_count]

    # 3. Load event config
    events, event_names, raw_probs = load_events()
    print("\nEvent tiers (from events.json):")
    for i, (name, raw) in enumerate(zip(event_names, raw_probs), 1):
        if isinstance(raw, str):
            print(f"  [{i}] {name}  ({raw})")
        else:
            print(f"  [{i}] {name}  (<= {raw})")

    # 4. Select target event
    target = int(input(f"\nTarget event tier (1-{len(events)}): "))
    target_name = event_names[target - 1]

    # 5. n upper bound
    n_max = int(input("n upper bound: "))

    # 6. Optimize
    print(f"\nSearching n=1..{n_max} for best {target_name}...")
    best_n = find_best_n(n_max, k_gen, formulas, events, target)

    def _expected(p: float) -> float:
        """Expected attempts until first success (geometric distribution)."""
        return 1.0 / p if p > 0 else float("inf")

    def _pity99(p: float) -> int | float:
        """Attempts needed for >= 99% chance of at least one success."""
        if p <= 0:
            return float("inf")
        if p >= 0.99:
            return 1
        return math.ceil(math.log(0.01) / math.log(1.0 - p))

    # Show probability curve across n
    print(f"\n  P({target_name}) vs n:")
    print(f"  {'n':<6} {'P':<14} {'E[attempts]':<14} {'pity99':<10}")
    print(f"  {'-' * 44}")
    for n in range(1, n_max + 1):
        p = prob_event(n, k_gen, formulas, events, target)
        marker = "  <-- best" if n == best_n else ""
        exp = _expected(p)
        pity = _pity99(p)
        exp_str = f"{exp:.1f}" if exp != float("inf") else "inf"
        pity_str = str(pity) if pity != float("inf") else "inf"
        print(f"  {n:<6} {p:.6f}   {exp_str:<14} {pity_str:<10}{marker}")


if __name__ == "__main__":
    main()

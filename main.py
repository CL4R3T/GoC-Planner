"""Event Optimizer — interactive CLI."""

from goc_python import find_best_n, ladder_tiers, prob_event

from core.stats import expected_attempts, pity99
from generators import ALL as all_generators


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
    _, _, all_formulas = load_generator(choice)

    # 2. Formula list
    print(f"\nFormulas (unlock order, {len(all_formulas)} total):")
    for i, f in enumerate(all_formulas, 1):
        print(f"  [{i}] {f.name}")
    if len(all_formulas) == 0:
        print("  (No formulas yet. Add them in generators/coin.py)")
        return
    f_count = int(input(f"\nUnlocked formula count (1-{len(all_formulas)}): "))

    # 3. Load event config
    tiers = ladder_tiers()
    print("\nEvent tiers (from ladder.toml):")
    for i, (name, grade, raw, _threshold) in enumerate(tiers, 1):
        print(f"  [{i:<2}] ({grade:<10}) {name}  ({raw})")

    # 4. Select target event
    target = int(input(f"\nTarget event tier (1-{len(tiers)}): "))
    target_name = tiers[target - 1][0]

    # 5. n upper bound
    n_max = int(input("n upper bound: "))

    # 6. Optimize
    print(f"\nSearching n=1..{n_max} for best {target_name}...")
    best_n = find_best_n(n_max, f_count, target)

    # Show probability curve across n
    print(f"\n  P({target_name}) vs n:")
    print(f"  {'n':<6} {'P':<16} {'E[attempts]':<14} {'pity99':<10}")
    print(f"  {'-' * 48}")
    for n in range(1, n_max + 1):
        p = prob_event(n, f_count, target)
        marker = "  <-- best" if n == best_n else ""
        exp = expected_attempts(p)
        p99 = pity99(p)
        exp_str = f"{exp:.1f}" if exp != float("inf") else "inf"
        pity_str = str(p99) if p99 != float("inf") else "inf"
        print(f"  {n:<6} {p:.10f}   {exp_str:<14} {pity_str:<10}{marker}")


if __name__ == "__main__":
    main()

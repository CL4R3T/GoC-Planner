"""Event Optimizer — Web GUI backend."""

from flask import Flask, jsonify, render_template, request

from core.config import GRADE_COLORS, GRADE_ORDER, load_ladder
from core.engine import find_best_n, full_distribution, prob_event
from core.stats import expected_attempts, pity99
from generators import ALL as all_generators

app = Flask(__name__)


# ── routes ───────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    """Serve the single-page app."""
    return render_template("index.html")


@app.route("/api/config")
def api_config():
    """Return generators, formulas, events for the frontend to build the UI."""
    events = load_ladder()

    generators = []
    for i, mod in enumerate(all_generators):
        name = mod.__name__.split(".")[-1]
        formulas = [{"index": j, "name": f.name} for j, f in enumerate(mod.FORMULAS)]
        generators.append(
            {
                "index": i,
                "name": name,
                "k": mod.K,
                "formulas": formulas,
            }
        )

    event_list = []
    for i, tier in enumerate(events.tiers):
        event_list.append(
            {
                "index": i,
                "name": tier.name,
                "probability": tier.raw,
                "value": float(tier.threshold),
                "grade": tier.grade,
            }
        )

    return jsonify(
        {
            "generators": generators,
            "events": event_list,
            "grades": GRADE_ORDER,
            "grade_colors": GRADE_COLORS,
        }
    )


@app.route("/api/optimize", methods=["POST"])
def api_optimize():
    """Run optimization and return curve + distribution data."""
    body = request.get_json()

    gen_idx = body["generator_idx"]
    f_count = body["formula_count"]
    target_event = body["target_event"]  # 1-indexed
    n_max = body["n_max"]

    # Load generator
    mod = all_generators[gen_idx]
    k_gen = mod.K
    formulas = mod.FORMULAS[:f_count]

    # Load events
    events = load_ladder()

    # Find best n
    best_n = find_best_n(n_max, k_gen, formulas, events, target_event)
    best_prob = prob_event(best_n, k_gen, formulas, events, target_event)

    # Build probability curve for all n
    curve = []
    for n in range(1, n_max + 1):
        p = prob_event(n, k_gen, formulas, events, target_event)
        exp = expected_attempts(p)
        p99 = pity99(p)
        curve.append(
            {
                "n": n,
                "prob": round(p, 12),
                "expected": round(exp, 1) if exp != float("inf") else None,
                "pity99": p99 if p99 != float("inf") else None,
                "is_best": n == best_n,
            }
        )

    # Full distribution at best_n
    dist_probs = full_distribution(best_n, k_gen, formulas, events)
    distribution = []
    for i, (tier, p) in enumerate(zip(events.tiers, dist_probs)):
        distribution.append(
            {
                "index": i,
                "name": tier.name,
                "grade": tier.grade,
                "prob": round(p, 12),
                "is_target": (i + 1) == target_event,
            }
        )

    best_exp = expected_attempts(best_prob)
    best_pity = pity99(best_prob)

    return jsonify(
        {
            "best_n": best_n,
            "best_prob": round(best_prob, 12),
            "best_expected": round(best_exp, 1) if best_exp != float("inf") else None,
            "best_pity99": best_pity if best_pity != float("inf") else None,
            "target_name": events.tiers[target_event - 1].name,
            "curve": curve,
            "distribution": distribution,
        }
    )


@app.route("/api/distribution", methods=["POST"])
def api_distribution():
    """Return full event distribution at a specific n."""
    body = request.get_json()
    gen_idx = body["generator_idx"]
    f_count = body["formula_count"]
    n = body["n"]

    mod = all_generators[gen_idx]
    k_gen = mod.K
    formulas = mod.FORMULAS[:f_count]

    events = load_ladder()
    dist_probs = full_distribution(n, k_gen, formulas, events)

    distribution = []
    for i, (tier, p) in enumerate(zip(events.tiers, dist_probs)):
        distribution.append(
            {
                "index": i,
                "name": tier.name,
                "grade": tier.grade,
                "prob": round(p, 12),
            }
        )
    return jsonify({"n": n, "distribution": distribution})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

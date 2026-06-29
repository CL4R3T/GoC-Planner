"""Event Optimizer — Web GUI backend."""

from flask import Flask, jsonify, render_template, request
from goc_python import find_best_n, full_distribution, ladder_tiers, prob_event

from core.stats import expected_attempts, pity99
from generators import ALL as all_generators

app = Flask(__name__)

GRADE_ORDER = ["blue", "purple", "golden", "diamond", "legendary", "impossible"]
GRADE_COLORS = {
    "blue": "#58a6ff",
    "purple": "#bc8cff",
    "golden": "#e3b341",
    "diamond": "#56d4dd",
    "legendary": "#ffa657",
    "impossible": "#f85149",
}


# ── helpers ──────────────────────────────────────────────────────────────────


def _json_body():
    """Return the request JSON, tolerating a missing/invalid body."""
    return request.get_json(silent=True) or {}


def _as_int(body, key, default):
    """Coerce a body field to int, falling back to default on bad input."""
    try:
        return int(body.get(key, default))
    except (TypeError, ValueError):
        return default


def _optimize_params(body):
    """Extract and clamp the optimize-endpoint inputs from a request body.

    Keeps the Python-level ``tiers[target_event - 1]`` indexing in bounds and
    avoids handing out-of-range values to the Rust extension.
    """
    tiers = ladder_tiers()
    f_count = max(1, _as_int(body, "formula_count", 1))
    target_event = max(1, min(_as_int(body, "target_event", 1), len(tiers)))
    n_max = max(1, _as_int(body, "n_max", 1))
    return f_count, target_event, n_max


# ── routes ───────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    """Serve the single-page app."""
    return render_template("index.html")


@app.route("/api/config")
def api_config():
    """Return generators, formulas, events for the frontend to build the UI."""
    tiers = ladder_tiers()

    generators = []
    for i, mod in enumerate(all_generators):
        name = mod.__name__.split(".")[-1]
        formulas = [{"index": j, "name": f.name} for j, f in enumerate(mod.FORMULAS)]
        generators.append({"index": i, "name": name, "k": mod.K, "formulas": formulas})

    event_list = []
    for i, (name, grade, raw, threshold) in enumerate(tiers):
        event_list.append(
            {"index": i, "name": name, "probability": raw, "value": threshold, "grade": grade}
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
    body = _json_body()

    f_count, target_event, n_max = _optimize_params(body)

    tiers = ladder_tiers()

    best_n = find_best_n(n_max, f_count, target_event)
    best_prob = prob_event(best_n, f_count, target_event)

    curve = []
    for n in range(1, n_max + 1):
        p = prob_event(n, f_count, target_event)
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

    dist_probs = full_distribution(best_n, f_count)
    distribution = []
    for i, ((name, grade, _raw, _threshold), p) in enumerate(zip(tiers, dist_probs)):
        distribution.append(
            {
                "index": i,
                "name": name,
                "grade": grade,
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
            "target_name": tiers[target_event - 1][0],
            "curve": curve,
            "distribution": distribution,
        }
    )


@app.route("/api/distribution", methods=["POST"])
def api_distribution():
    """Return full event distribution at a specific n."""
    body = _json_body()

    # formula_count is clamped by the Rust extension; coerce and guard n >= 1.
    f_count = max(1, _as_int(body, "formula_count", 1))
    n = max(1, _as_int(body, "n", 1))

    tiers = ladder_tiers()
    dist_probs = full_distribution(n, f_count)

    distribution = []
    for i, ((name, grade, _raw, _threshold), p) in enumerate(zip(tiers, dist_probs)):
        distribution.append({"index": i, "name": name, "grade": grade, "prob": round(p, 12)})
    return jsonify({"n": n, "distribution": distribution})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

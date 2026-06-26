"""Event Optimizer — Web GUI backend."""

import json
import math
import os

from flask import Flask, jsonify, render_template, request

from core.engine import find_best_n, prob_event, full_distribution
from core.events import Events
from generators import ALL as all_generators

app = Flask(__name__)


# ── helpers (mirror main.py) ────────────────────────────────────────────────

def _parse_prob(value) -> float:
    """Parse probability: float or '1/N' string."""
    if isinstance(value, (int, float)):
        return float(value)
    s = value.replace(",", "")
    if s.startswith("1/"):
        return 1.0 / int(s[2:])
    return float(s)


def _load_events() -> tuple[Events, list[str], list]:
    """Load event config from events.json."""
    path = os.path.join(os.path.dirname(__file__), "events.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    names = [entry["name"] for entry in data]
    raw_probs = [entry["probability"] for entry in data]
    thresholds = [_parse_prob(p) for p in raw_probs]
    return Events(thresholds), names, raw_probs


def _format_prob(raw) -> str:
    """Format a raw probability for display."""
    if isinstance(raw, str):
        return raw
    return str(raw)


def _expected(p: float) -> float:
    """Expected attempts until first success."""
    return 1.0 / p if p > 0 else float("inf")


def _pity99(p: float) -> int | float:
    """Attempts needed for >= 99% chance of at least one success."""
    if p <= 0:
        return float("inf")
    if p >= 0.99:
        return 1
    return math.ceil(math.log(0.01) / math.log(1.0 - p))


# ── routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the single-page app."""
    return render_template("index.html")


@app.route("/api/config")
def api_config():
    """Return generators, formulas, events for the frontend to build the UI."""
    events, event_names, raw_probs = _load_events()

    generators = []
    for i, mod in enumerate(all_generators):
        name = mod.__name__.split(".")[-1]
        formulas = [{"index": j, "name": f.name} for j, f in enumerate(mod.FORMULAS)]
        generators.append({
            "index": i,
            "name": name,
            "k": mod.K,
            "formulas": formulas,
        })

    event_list = []
    for i, (ename, raw) in enumerate(zip(event_names, raw_probs)):
        event_list.append({
            "index": i,
            "name": ename,
            "probability": _format_prob(raw),
            "value": _parse_prob(raw),
        })

    return jsonify({
        "generators": generators,
        "events": event_list,
    })


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
    events, event_names, raw_probs = _load_events()

    # Find best n
    best_n = find_best_n(n_max, k_gen, formulas, events, target_event)
    best_prob = prob_event(best_n, k_gen, formulas, events, target_event)

    # Build probability curve for all n
    curve = []
    for n in range(1, n_max + 1):
        p = prob_event(n, k_gen, formulas, events, target_event)
        exp = _expected(p)
        pity = _pity99(p)
        curve.append({
            "n": n,
            "prob": round(p, 8),
            "expected": round(exp, 1) if exp != float("inf") else None,
            "pity99": pity if pity != float("inf") else None,
            "is_best": n == best_n,
        })

    # Full distribution at best_n
    dist_probs = full_distribution(best_n, k_gen, formulas, events)
    distribution = []
    for i, (ename, p) in enumerate(zip(event_names, dist_probs)):
        distribution.append({
            "index": i,
            "name": ename,
            "prob": round(p, 8),
            "is_target": (i + 1) == target_event,
        })

    best_exp = _expected(best_prob)
    best_pity = _pity99(best_prob)

    return jsonify({
        "best_n": best_n,
        "best_prob": round(best_prob, 8),
        "best_expected": round(best_exp, 1) if best_exp != float("inf") else None,
        "best_pity99": best_pity if best_pity != float("inf") else None,
        "target_name": event_names[target_event - 1],
        "curve": curve,
        "distribution": distribution,
    })


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

    events, event_names, _ = _load_events()
    dist_probs = full_distribution(n, k_gen, formulas, events)

    distribution = []
    for i, (ename, p) in enumerate(zip(event_names, dist_probs)):
        distribution.append({
            "index": i,
            "name": ename,
            "prob": round(p, 8),
        })
    return jsonify({"n": n, "distribution": distribution})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

import {
  initSync,
  ladder_tiers,
  formula_names,
  prob_event,
  find_best_n,
  full_distribution,
  expected_attempts,
  pity99,
} from "./pkg/goc_wasm.js";

const GRADE_ORDER = ["blue", "purple", "golden", "diamond", "legendary", "impossible"];
const GRADE_COLORS = {
  blue: "#58a6ff",
  purple: "#bc8cff",
  golden: "#e3b341",
  diamond: "#56d4dd",
  legendary: "#ffa657",
  impossible: "#f85149",
};

const round12 = (x) => Number(x.toFixed(12));
const round1 = (x) => Number(x.toFixed(1));
const finite1 = (x) => (Number.isFinite(x) ? round1(x) : null);
const finitePity = (x) => (Number.isFinite(x) ? x : null);

function buildConfig() {
  const formulas = formula_names().map((name, i) => ({ index: i, name }));
  const events = ladder_tiers().map((t, i) => ({
    index: i,
    name: t.name,
    probability: t.raw,
    value: t.threshold,
    grade: t.grade,
  }));
  return {
    generators: [{ index: 0, name: "coin", k: 2, formulas }],
    events,
    grades: GRADE_ORDER,
    grade_colors: GRADE_COLORS,
  };
}

function buildDistribution(n, fCount) {
  const probs = full_distribution(n, fCount);
  const tiers = ladder_tiers();
  const distribution = tiers.map((t, i) => ({
    index: i,
    name: t.name,
    grade: t.grade,
    prob: round12(probs[i]),
  }));
  return { n, distribution };
}

function buildOptimize(nMax, fCount, target) {
  const bestN = find_best_n(nMax, fCount, target);
  const bestProb = prob_event(bestN, fCount, target);

  const curve = [];
  for (let n = 1; n <= nMax; n++) {
    const p = prob_event(n, fCount, target);
    curve.push({
      n,
      prob: round12(p),
      expected: finite1(expected_attempts(p)),
      pity99: finitePity(pity99(p)),
      is_best: n === bestN,
    });
  }

  const distProbs = full_distribution(bestN, fCount);
  const tiers = ladder_tiers();
  const distribution = tiers.map((t, i) => ({
    index: i,
    name: t.name,
    grade: t.grade,
    prob: round12(distProbs[i]),
    is_target: i + 1 === target,
  }));

  return {
    best_n: bestN,
    best_prob: round12(bestProb),
    best_expected: finite1(expected_attempts(bestProb)),
    best_pity99: finitePity(pity99(bestProb)),
    target_name: tiers[target - 1].name,
    curve,
    distribution,
  };
}

function handle(e) {
  const { id, type } = e.data;
  try {
    let result;
    if (type === "config") result = buildConfig();
    else if (type === "optimize") result = buildOptimize(e.data.n_max, e.data.formula_count, e.data.target_event);
    else if (type === "distribution") result = buildDistribution(e.data.n, e.data.formula_count);
    self.postMessage({ id, result });
  } catch (err) {
    self.postMessage({ id, error: String(err) });
  }
}

let ready = false;
let failed = false;
const queue = [];
self.onmessage = (e) => {
  const id = e.data && e.data.id;
  if (failed) {
    self.postMessage({ id, error: "wasm init failed" });
    return;
  }
  if (!ready) {
    queue.push(e);
    return;
  }
  handle(e);
};

(async () => {
  try {
    const resp = await fetch("./pkg/goc_wasm_bg.wasm");
    initSync(new Uint8Array(await resp.arrayBuffer()));
    ready = true;
    for (const e of queue) handle(e);
  } catch (err) {
    failed = true;
    const msg = "wasm init failed: " + String(err);
    for (const e of queue) self.postMessage({ id: e.data && e.data.id, error: msg });
    queue.length = 0;
  }
})();

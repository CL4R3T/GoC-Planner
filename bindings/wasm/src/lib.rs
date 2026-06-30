use goc_core::games::GameFormula;
use goc_core::games::coin::CoinFormula;
use goc_core::ladder::Ladder;
use goc_core::planner;
use goc_core::stats;
use num_traits::ToPrimitive;
use serde::Serialize;
use wasm_bindgen::prelude::*;

#[derive(Serialize)]
struct TierInfo {
    name: String,
    grade: String,
    raw: String,
    threshold: f64,
}

// wasm is single-threaded and OnceLock needs +atomics; a thread_local caches the
// parsed ladder (parsed once) without re-parsing TOML on every exported call.
thread_local! {
    static LADDER: Ladder = Ladder::baked();
}

fn with_ladder<R>(f: impl FnOnce(&Ladder) -> R) -> R {
    LADDER.with(f)
}

#[wasm_bindgen]
pub fn ladder_tiers() -> Result<JsValue, JsValue> {
    with_ladder(|ladder| {
        let tiers: Vec<TierInfo> = ladder
            .tiers()
            .iter()
            .map(|t| TierInfo {
                name: t.name.clone(),
                grade: t.grade.clone(),
                raw: t.raw.clone(),
                threshold: t.threshold.to_f64().unwrap_or(0.0),
            })
            .collect();
        serde_wasm_bindgen::to_value(&tiers).map_err(Into::into)
    })
}

#[wasm_bindgen]
pub fn formula_names() -> Vec<String> {
    CoinFormula::all()
        .iter()
        .map(|f| f.name().to_string())
        .collect()
}

#[wasm_bindgen]
pub fn prob_event(n: usize, f_count: usize, target: usize) -> f64 {
    let all = CoinFormula::all();
    let formulas = &all[..f_count.min(all.len())];
    with_ladder(|ladder| {
        let target = target.clamp(1, ladder.len());
        planner::prob_event(n, 2, formulas, ladder, target)
            .to_f64()
            .unwrap_or(0.0)
    })
}

#[wasm_bindgen]
pub fn find_best_n(n_max: usize, f_count: usize, target: usize) -> usize {
    let all = CoinFormula::all();
    let formulas = &all[..f_count.min(all.len())];
    with_ladder(|ladder| {
        let target = target.clamp(1, ladder.len());
        planner::find_best_n(n_max, 2, formulas, ladder, target)
    })
}

#[wasm_bindgen]
pub fn full_distribution(n: usize, f_count: usize) -> Vec<f64> {
    let all = CoinFormula::all();
    let formulas = &all[..f_count.min(all.len())];
    with_ladder(|ladder| {
        planner::full_distribution(n, 2, formulas, ladder)
            .iter()
            .map(|r| r.to_f64().unwrap_or(0.0))
            .collect()
    })
}

#[wasm_bindgen]
pub fn expected_attempts(p: f64) -> f64 {
    stats::expected_attempts(p)
}

#[wasm_bindgen]
pub fn pity99(p: f64) -> f64 {
    stats::pity99(p)
}

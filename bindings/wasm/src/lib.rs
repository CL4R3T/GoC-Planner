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

#[wasm_bindgen]
pub fn ladder_tiers() -> Result<JsValue, JsValue> {
    let tiers: Vec<TierInfo> = Ladder::baked()
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
    planner::prob_event(n, 2, &all[..f_count], &Ladder::baked(), target)
        .to_f64()
        .unwrap_or(0.0)
}

#[wasm_bindgen]
pub fn find_best_n(n_max: usize, f_count: usize, target: usize) -> usize {
    let all = CoinFormula::all();
    planner::find_best_n(n_max, 2, &all[..f_count], &Ladder::baked(), target)
}

#[wasm_bindgen]
pub fn full_distribution(n: usize, f_count: usize) -> Vec<f64> {
    let all = CoinFormula::all();
    planner::full_distribution(n, 2, &all[..f_count], &Ladder::baked())
        .iter()
        .map(|r| r.to_f64().unwrap_or(0.0))
        .collect()
}

#[wasm_bindgen]
pub fn expected_attempts(p: f64) -> f64 {
    stats::expected_attempts(p)
}

#[wasm_bindgen]
pub fn pity99(p: f64) -> f64 {
    stats::pity99(p)
}

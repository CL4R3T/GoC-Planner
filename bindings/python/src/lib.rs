#[pyo3::pymodule]
mod goc_python {
    use goc_core::games::GameFormula;
    use goc_core::games::coin::CoinFormula;
    use goc_core::ladder::Ladder;
    use goc_core::planner;
    use num_traits::ToPrimitive;

    #[pyo3::pyfunction]
    fn ladder_tiers() -> Vec<(String, String, String, f64)> {
        Ladder::default_ladder()
            .tiers()
            .iter()
            .map(|t| {
                (
                    t.name.clone(),
                    t.grade.clone(),
                    t.raw.clone(),
                    t.threshold.to_f64().unwrap_or(0.0),
                )
            })
            .collect()
    }

    /// Clamp a formula count to the number of available formulas so an
    /// out-of-range value from untrusted input can never panic the slice.
    fn clamp_f_count(f_count: usize) -> usize {
        let total = CoinFormula::all().len();
        f_count.min(total)
    }

    /// Clamp a target tier index into the valid `1..=len` range so an
    /// out-of-range value never indexes out of bounds in `interval_bounds`.
    fn clamp_target(target: usize) -> usize {
        let len = Ladder::default_ladder().len();
        target.clamp(1, len)
    }

    #[pyo3::pyfunction]
    fn prob_event(n: usize, f_count: usize, target: usize) -> f64 {
        let all = CoinFormula::all();
        let f_count = clamp_f_count(f_count);
        let target = clamp_target(target);
        planner::prob_event(n, 2, &all[..f_count], Ladder::default_ladder(), target)
            .to_f64()
            .unwrap_or(0.0)
    }

    #[pyo3::pyfunction]
    fn find_best_n(n_max: usize, f_count: usize, target: usize) -> usize {
        let all = CoinFormula::all();
        let f_count = clamp_f_count(f_count);
        let target = clamp_target(target);
        planner::find_best_n(n_max, 2, &all[..f_count], Ladder::default_ladder(), target)
    }

    #[pyo3::pyfunction]
    fn full_distribution(n: usize, f_count: usize) -> Vec<f64> {
        let all = CoinFormula::all();
        let f_count = clamp_f_count(f_count);
        planner::full_distribution(n, 2, &all[..f_count], Ladder::default_ladder())
            .iter()
            .map(|r| r.to_f64().unwrap_or(0.0))
            .collect()
    }
}

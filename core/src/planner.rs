use num_bigint::{BigInt, BigUint, Sign};
use num_rational::BigRational;
use num_traits::{One, Zero};

use crate::games::{GameFormula, Mode};
use crate::ladder::Ladder;

fn to_bi(x: &BigUint) -> BigInt {
    BigInt::from_biguint(Sign::Plus, x.clone())
}

fn le(count: &BigUint, denom: &BigUint, thresh: &BigRational) -> bool {
    to_bi(count) * thresh.denom() <= thresh.numer() * to_bi(denom)
}

fn gt(count: &BigUint, denom: &BigUint, thresh: &BigRational) -> bool {
    to_bi(count) * thresh.denom() > thresh.numer() * to_bi(denom)
}

pub fn count_in_interval<F: GameFormula>(
    formula: &F,
    n: usize,
    denom: &BigUint,
    p_lower: &BigRational,
    p_upper: &BigRational,
) -> BigUint {
    let freqs = formula.freqs(n);
    match formula.mode() {
        Mode::AtLeast => {
            let x_low = (1..=n).find(|&x| le(&freqs[x], denom, p_upper));
            match x_low {
                None => BigUint::zero(),
                Some(xl) => {
                    let x_high = (1..=n).find(|&x| le(&freqs[x], denom, p_lower));
                    let ch = x_high.map_or(BigUint::zero(), |xh| freqs[xh].clone());
                    freqs[xl].clone() - ch
                }
            }
        }
        Mode::Exact => {
            let mut total = BigUint::zero();
            for c in freqs.iter().skip(1) {
                if c.is_zero() {
                    continue;
                }
                if le(c, denom, p_upper) && gt(c, denom, p_lower) {
                    total += c;
                }
            }
            total
        }
        Mode::A => {
            let count = &freqs[0];
            if count.is_zero() || !le(count, denom, p_upper) || !gt(count, denom, p_lower) {
                BigUint::zero()
            } else {
                count.clone()
            }
        }
    }
}

pub fn prob_event<F: GameFormula>(
    n: usize,
    s: usize,
    formulas: &[F],
    ladder: &Ladder,
    target: usize,
) -> BigRational {
    let denom = BigUint::from(s).pow(n as u32);
    let (p_upper, p_lower) = ladder.interval_bounds(target);
    let mut prob_no = BigRational::one();
    for f in formulas {
        let count = count_in_interval(f, n, &denom, &p_lower, &p_upper);
        if count.is_zero() {
            continue;
        }
        let p_f = BigRational::new(to_bi(&count), to_bi(&denom));
        prob_no *= BigRational::one() - p_f;
    }
    BigRational::one() - prob_no
}

pub fn find_best_n<F: GameFormula>(
    n_max: usize,
    s: usize,
    formulas: &[F],
    ladder: &Ladder,
    target: usize,
) -> usize {
    let mut best_n = 1;
    let mut best: Option<BigRational> = None;
    for n in 1..=n_max {
        let p = prob_event(n, s, formulas, ladder, target);
        if best.as_ref().is_none_or(|b| p > *b) {
            best = Some(p);
            best_n = n;
        }
    }
    best_n
}

pub fn full_distribution<F: GameFormula>(
    n: usize,
    s: usize,
    formulas: &[F],
    ladder: &Ladder,
) -> Vec<BigRational> {
    let denom = BigUint::from(s).pow(n as u32);
    let m = ladder.len();
    let mut probs_no = vec![BigRational::one(); m];
    for f in formulas {
        for k in 1..=m {
            let (p_upper, p_lower) = ladder.interval_bounds(k);
            let count = count_in_interval(f, n, &denom, &p_lower, &p_upper);
            if count.is_zero() {
                continue;
            }
            let p_f = BigRational::new(to_bi(&count), to_bi(&denom));
            probs_no[k - 1] *= BigRational::one() - p_f;
        }
    }
    probs_no
        .into_iter()
        .map(|pn| BigRational::one() - pn)
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::games::coin::CoinFormula;
    use serde::Deserialize;

    fn ladder() -> Ladder {
        Ladder::from_toml(include_str!("../../ladder.toml")).unwrap()
    }

    #[derive(Deserialize)]
    struct Frac {
        n: String,
        d: String,
    }

    #[derive(Deserialize)]
    struct Best {
        target: usize,
        best_n: usize,
        prob: Frac,
    }

    #[derive(Deserialize)]
    struct Dist {
        n: usize,
        probs: Vec<Frac>,
    }

    #[derive(Deserialize)]
    struct Golden {
        k: usize,
        best: Vec<Best>,
        dist: Vec<Dist>,
    }

    fn golden() -> Golden {
        serde_json::from_str(include_str!("../testdata/planner_golden.json")).unwrap()
    }

    fn fr_eq(p: &BigRational, f: &Frac) -> bool {
        p.numer().to_string() == f.n && p.denom().to_string() == f.d
    }

    #[test]
    fn parity_prob_and_best_n() {
        let g = golden();
        let ladder = ladder();
        let formulas = CoinFormula::all();
        for b in &g.best {
            let bn = find_best_n(30, g.k, &formulas, &ladder, b.target);
            assert_eq!(bn, b.best_n, "best_n target {}", b.target);
            let p = prob_event(bn, g.k, &formulas, &ladder, b.target);
            assert!(fr_eq(&p, &b.prob), "prob target {} best_n {}", b.target, bn);
        }
    }

    #[test]
    fn parity_distribution() {
        let g = golden();
        let ladder = ladder();
        let formulas = CoinFormula::all();
        for d in &g.dist {
            let dist = full_distribution(d.n, g.k, &formulas, &ladder);
            assert_eq!(dist.len(), d.probs.len(), "n={}", d.n);
            for (i, (p, f)) in dist.iter().zip(d.probs.iter()).enumerate() {
                assert!(fr_eq(p, f), "dist n={} tier {}", d.n, i);
            }
        }
    }
}

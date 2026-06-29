use std::collections::HashMap;
use std::sync::OnceLock;

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use serde::Deserialize;

const GRADE_COUNTS: [(&str, u32); 6] = [
    ("blue", 20),
    ("purple", 8),
    ("golden", 7),
    ("diamond", 5),
    ("legendary", 4),
    ("impossible", 2),
];

#[derive(Debug, Clone)]
pub struct Tier {
    pub name: String,
    pub grade: String,
    pub threshold: BigRational,
    pub raw: String,
}

pub struct Ladder {
    tiers: Vec<Tier>,
}

#[derive(Deserialize)]
struct RawLadder {
    events: Vec<RawEvent>,
}

#[derive(Deserialize)]
struct RawEvent {
    prob: String,
    grade: String,
    desc: String,
}

impl Ladder {
    pub fn from_toml(toml_str: &str) -> Result<Self, String> {
        let raw: RawLadder = toml::from_str(toml_str).map_err(|e| e.to_string())?;

        let mut tiers: Vec<Tier> = raw
            .events
            .into_iter()
            .map(|e| Tier {
                name: clean_name(&e.desc),
                grade: e.grade,
                threshold: parse_prob(&e.prob),
                raw: e.prob,
            })
            .collect();

        for t in &tiers {
            if !GRADE_COUNTS.iter().any(|(g, _)| *g == t.grade) {
                return Err(format!("unknown grade {:?}", t.grade));
            }
        }

        tiers.sort_by(|a, b| b.threshold.cmp(&a.threshold));

        for w in tiers.windows(2) {
            if w[0].threshold <= w[1].threshold {
                return Err("tiers not strictly descending".into());
            }
        }

        let mut counts: HashMap<&str, u32> = HashMap::new();
        for t in &tiers {
            *counts.entry(t.grade.as_str()).or_insert(0) += 1;
        }
        for (g, c) in GRADE_COUNTS {
            if counts.get(g).copied().unwrap_or(0) != c {
                return Err(format!("grade {g:?} count != {c}"));
            }
        }

        Ok(Ladder { tiers })
    }

    pub fn default_ladder() -> &'static Ladder {
        static LADDER: OnceLock<Ladder> = OnceLock::new();
        LADDER.get_or_init(|| Ladder::from_toml(include_str!("../../ladder.toml")).unwrap())
    }

    pub fn tiers(&self) -> &[Tier] {
        &self.tiers
    }

    pub fn len(&self) -> usize {
        self.tiers.len()
    }

    pub fn is_empty(&self) -> bool {
        self.tiers.is_empty()
    }

    pub fn interval_bounds(&self, k: usize) -> (BigRational, BigRational) {
        let p_upper = self.tiers[k - 1].threshold.clone();
        let p_lower = if k < self.tiers.len() {
            self.tiers[k].threshold.clone()
        } else {
            BigRational::zero()
        };
        (p_upper, p_lower)
    }
}

pub fn parse_prob(raw: &str) -> BigRational {
    let s = raw.trim().replace(',', "");
    if let Some(pct) = s.strip_suffix('%') {
        return decimal(pct) / decimal("100");
    }
    if let Some((n, d)) = s.split_once('/') {
        return rat(n.parse().unwrap(), d.parse().unwrap());
    }
    decimal(&s)
}

fn rat(n: BigInt, d: BigInt) -> BigRational {
    BigRational::new(n, d)
}

fn decimal(s: &str) -> BigRational {
    if let Some((intp, fracp)) = s.split_once('.') {
        let numer: BigInt = format!("{intp}{fracp}").parse().unwrap();
        let denom = BigInt::from(10u32).pow(fracp.len() as u32);
        rat(numer, denom)
    } else {
        rat(s.parse().unwrap(), BigInt::from(1u32))
    }
}

fn clean_name(desc: &str) -> String {
    desc.strip_prefix("...").unwrap_or(desc).trim().to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parity_with_python() {
        let ladder = Ladder::from_toml(include_str!("../../ladder.toml")).unwrap();
        #[derive(serde::Deserialize)]
        struct GoldTier {
            name: String,
            grade: String,
            n: String,
            d: String,
            raw: String,
        }
        let gold: Vec<GoldTier> =
            serde_json::from_str(include_str!("../testdata/ladder_golden.json")).unwrap();
        assert_eq!(ladder.tiers.len(), gold.len());
        for (t, g) in ladder.tiers.iter().zip(gold.iter()) {
            assert_eq!(t.name, g.name, "name @ {}", g.raw);
            assert_eq!(t.grade, g.grade, "grade @ {}", g.raw);
            assert_eq!(t.raw, g.raw, "raw @ {}", g.raw);
            assert_eq!(t.threshold.numer().to_string(), g.n, "numer @ {}", g.raw);
            assert_eq!(t.threshold.denom().to_string(), g.d, "denom @ {}", g.raw);
        }
    }

    #[test]
    fn invariants() {
        let ladder = Ladder::from_toml(include_str!("../../ladder.toml")).unwrap();
        assert_eq!(ladder.len(), 46);
        for w in ladder.tiers.windows(2) {
            assert!(w[0].threshold > w[1].threshold);
        }
        let (up, lo) = ladder.interval_bounds(1);
        assert_eq!(up, rat(BigInt::from(1), BigInt::from(10)));
        assert_eq!(lo, rat(BigInt::from(19), BigInt::from(200)));
        let (up_last, lo_last) = ladder.interval_bounds(46);
        assert_eq!(lo_last, BigRational::zero());
        assert_eq!(up_last, rat(BigInt::from(1), BigInt::from(292201338)));
    }

    #[test]
    fn default_ladder_singleton() {
        assert!(std::ptr::eq(
            Ladder::default_ladder(),
            Ladder::default_ladder()
        ));
        assert_eq!(Ladder::default_ladder().len(), 46);
    }
}

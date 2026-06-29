use std::{collections::HashMap, fmt::Debug};

use num_bigint::BigUint;
use num_traits::{ToPrimitive, Zero};

pub mod coin;

pub trait BaseGame<V = usize> {
    const STATES: usize;

    type Formula: GameFormula;

    fn all_states_with(n: usize) -> BaseGameSeqEnumerator {
        BaseGameSeqEnumerator::new(Self::STATES, n)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    AtLeast,
    Exact,
    A,
}

pub trait GameFormula: Sized {
    fn all() -> Vec<Self>;
    fn freqs(&self, n: usize) -> Vec<BigUint>;
    fn mode(&self) -> Mode;
}

pub struct BaseGameSeqEnumerator {
    n: usize,
    s: usize,
    i: BigUint,
}

impl BaseGameSeqEnumerator {
    pub fn new(s: usize, n: usize) -> Self {
        let total = BigUint::from(s).pow(n as u32);
        Self { n, s, i: total }
    }
}

impl Iterator for BaseGameSeqEnumerator {
    type Item = Vec<usize>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.i.is_zero() {
            return None;
        }
        self.i -= 1u32;
        let mut res = Vec::with_capacity(self.n);
        let mut i = self.i.clone();
        for _ in 0..self.n {
            res.push((i.clone() % self.s).to_usize().unwrap());
            i /= self.s;
        }
        Some(res)
    }
}

pub trait Dist<V> {
    fn solve(n: usize) -> Self;

    fn freq(&self, val: &V) -> BigUint;
    fn total(&self) -> BigUint;

    fn all_values(&self) -> Vec<V>;
    fn all_freqs(&self) -> Vec<BigUint> {
        self.all_values()
            .into_iter()
            .map(|v| self.freq(&v))
            .collect()
    }
    fn all_pairs(&self) -> Vec<(V, BigUint)> {
        self.all_values()
            .into_iter()
            .map(|v| {
                let f = self.freq(&v);
                (v, f)
            })
            .collect()
    }
}

pub trait Statistic<G: BaseGame, D, V>
where
    D: Dist<V>,
{
    /// This should be something like (Fin n -> Fin (G::STATES)) -> V
    fn eval(seq: &[usize]) -> V;
    fn dist(n: usize) -> D {
        D::solve(n)
    }
}

/// 后缀和：`out[x] = freqs[x] + freqs[x+1] + ... + freqs[last]`。
/// 用于 AtLeast 模式：把单点计数 cnt(v) 转成尾部计数 Σ_{v≥x} cnt(v)。
pub fn tail_sums(freqs: Vec<BigUint>) -> Vec<BigUint> {
    let mut out = freqs;
    for i in (0..out.len().saturating_sub(1)).rev() {
        let next = out[i + 1].clone();
        out[i] += next;
    }
    out
}

#[allow(dead_code)]
fn validate_with<F, G, D, V>(n: usize)
where
    F: Statistic<G, D, V>,
    G: BaseGame,
    D: Dist<V>,
    V: std::hash::Hash + Eq + Debug,
{
    let d = F::dist(n);
    let mut map = HashMap::new();
    let mut cnt = BigUint::zero();
    for seq in G::all_states_with(n) {
        let v = F::eval(&seq);
        *map.entry(v).or_insert(BigUint::zero()) += 1u32;
        cnt += 1u32;
    }
    assert_eq!(cnt, d.total(), "Total count mismatch for n={}", n);
    for (v, expected_freq) in map {
        let f = d.freq(&v);
        assert_eq!(
            f, expected_freq,
            "Frequency mismatch for value {:?} with n={}",
            v, n
        );
    }
}

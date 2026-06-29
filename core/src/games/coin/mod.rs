use num_bigint::BigUint;
use num_traits::Zero;

use crate::games::{BaseGame, Dist, GameFormula, Mode, Statistic, tail_sums};

pub mod head_count;
pub use head_count::Headcount;

pub mod longest_streak;
pub use longest_streak::LongestStreak;

pub struct CoinGame;

impl BaseGame for CoinGame {
    /// 1 for head, 0 for tail
    const STATES: usize = 2;

    type Formula = CoinFormula;
}

pub enum CoinFormula {
    AtLeastX,
    ExactX,
    LongestStreak,
    Alternating,
    PrimeCount,
}

impl GameFormula for CoinFormula {
    fn all() -> Vec<Self> {
        vec![
            CoinFormula::AtLeastX,
            CoinFormula::ExactX,
            CoinFormula::LongestStreak,
            CoinFormula::Alternating,
            CoinFormula::PrimeCount,
        ]
    }

    fn freqs(&self, n: usize) -> Vec<BigUint> {
        match self {
            CoinFormula::ExactX => Headcount::dist(n).all_freqs(),
            CoinFormula::AtLeastX => tail_sums(Headcount::dist(n).all_freqs()),
            CoinFormula::LongestStreak => tail_sums(LongestStreak::dist(n).all_freqs()),
            CoinFormula::Alternating => alternating_freqs(n),
            CoinFormula::PrimeCount => prime_count_freqs(n),
        }
    }

    fn mode(&self) -> Mode {
        match self {
            CoinFormula::AtLeastX | CoinFormula::LongestStreak | CoinFormula::Alternating => {
                Mode::AtLeast
            }
            CoinFormula::ExactX => Mode::Exact,
            CoinFormula::PrimeCount => Mode::A,
        }
    }
}

fn alternating_freqs(n: usize) -> Vec<BigUint> {
    if n == 0 {
        return vec![BigUint::from(1u32)];
    }
    let ls = tail_sums(LongestStreak::dist(n - 1).all_freqs());
    let denom = BigUint::from(2u32) << (n - 1);
    let mut freqs = Vec::with_capacity(n + 1);
    freqs.push(denom.clone());
    for x in 1..=n {
        let v = ls.get(x - 1).cloned().unwrap_or_else(BigUint::zero);
        freqs.push(v << 1);
    }
    freqs
}

fn prime_count_freqs(n: usize) -> Vec<BigUint> {
    let hc = Headcount::dist(n).all_freqs();
    let mut total = BigUint::zero();
    for p in primes_upto(n) {
        total += &hc[p];
    }
    vec![total]
}

fn primes_upto(n: usize) -> Vec<usize> {
    if n < 2 {
        return Vec::new();
    }
    let mut sieve = vec![true; n + 1];
    sieve[0] = false;
    sieve[1] = false;
    let mut i = 2;
    while i * i <= n {
        if sieve[i] {
            let mut j = i * i;
            while j <= n {
                sieve[j] = false;
                j += i;
            }
        }
        i += 1;
    }
    (2..=n).filter(|&i| sieve[i]).collect()
}

#[cfg(test)]
mod tests {
    use num_bigint::BigUint;
    use num_traits::Zero;

    use super::*;

    fn longest_alternating(seq: &[usize]) -> usize {
        if seq.is_empty() {
            return 0;
        }
        let mut best = 1;
        let mut cur = 1;
        for w in seq.windows(2) {
            if w[0] != w[1] {
                cur += 1;
                if cur > best {
                    best = cur;
                }
            } else {
                cur = 1;
            }
        }
        best
    }

    fn brute<E: Fn(&[usize]) -> usize>(n: usize, eval: E) -> Vec<BigUint> {
        let mut cnt = vec![BigUint::zero(); n + 1];
        for seq in CoinGame::all_states_with(n) {
            let v = eval(&seq);
            assert!(v <= n, "value {v} out of range for n={n}");
            cnt[v] += 1u32;
        }
        cnt
    }

    fn suffix(cnt: &[BigUint]) -> Vec<BigUint> {
        let mut out = vec![BigUint::zero(); cnt.len()];
        let mut acc = BigUint::zero();
        for i in (0..cnt.len()).rev() {
            acc += &cnt[i];
            out[i] = acc.clone();
        }
        out
    }

    #[test]
    fn freqs_alternating() {
        for n in 1..=12 {
            let cnt = brute(n, longest_alternating);
            let exp = suffix(&cnt);
            let got = CoinFormula::Alternating.freqs(n);
            assert_eq!(got, exp, "Alternating n={n}");
        }
    }

    #[test]
    fn freqs_prime_count() {
        for n in 1..=12 {
            let primes = primes_upto(n);
            let mut exp = BigUint::zero();
            for seq in CoinGame::all_states_with(n) {
                let h: usize = seq.iter().sum();
                if primes.contains(&h) {
                    exp += 1u32;
                }
            }
            let got = CoinFormula::PrimeCount.freqs(n);
            assert_eq!(got.len(), 1, "PrimeCount n={n}");
            assert_eq!(got[0], exp, "PrimeCount n={n}");
        }
    }
}

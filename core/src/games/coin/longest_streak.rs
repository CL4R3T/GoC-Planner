use num_bigint::BigUint;
use num_traits::Zero;

use crate::games::{Dist, Statistic};

use super::CoinGame;

/// At least x heads in a row in n coins.
pub struct LongestStreak;

pub struct LongestStreakDist {
    total: BigUint,
    data: Vec<BigUint>,
}

impl Dist<usize> for LongestStreakDist {
    fn solve(n: usize) -> Self {
        let mut data = Vec::with_capacity(n + 1);
        let mut prev = BigUint::zero();
        for run_len in 0..=n {
            let f = longest_run_le(n, run_len);
            data.push(&f - &prev);
            prev = f;
        }

        Self {
            total: BigUint::from(1u32) << n,
            data,
        }
    }

    fn all_values(&self) -> Vec<usize> {
        (0..self.data.len()).collect()
    }

    fn freq(&self, val: &usize) -> BigUint {
        self.data[*val].clone()
    }

    fn total(&self) -> BigUint {
        self.total.clone()
    }
}

impl Statistic<CoinGame, LongestStreakDist, usize> for LongestStreak {
    fn eval(seq: &[usize]) -> usize {
        let mut best = 0;
        let mut cur = 0;
        for &x in seq {
            if x == 1 {
                cur += 1;
                if cur > best {
                    best = cur;
                }
            } else {
                cur = 0;
            }
        }
        best
    }
}

fn longest_run_le(n: usize, m: usize) -> BigUint {
    if n == 0 {
        return BigUint::from(1u32);
    }
    let win = m + 1;
    let mut a: Vec<BigUint> = Vec::with_capacity(n + 1);
    a.push(BigUint::from(1u32));
    let mut s = BigUint::from(1u32);
    for i in 1..=n {
        let mut ai = s.clone();
        if i <= m {
            ai += 1u32;
        }
        s = &s + &ai;
        if i >= win {
            s = &s - &a[i - win];
        }
        a.push(ai);
    }
    a[n].clone()
}

#[cfg(test)]
mod tests {
    use crate::games::validate_with;

    use super::*;

    #[test]
    fn test_longest_streak() {
        (1..=10).for_each(|n| validate_with::<LongestStreak, _, _, _>(n));
    }
}

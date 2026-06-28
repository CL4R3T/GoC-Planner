use num_bigint::BigUint;

use crate::games::{Dist, Statistic};

use super::CoinGame;

pub struct Headcount;

pub struct HeadcountDist {
    total: BigUint,
    data: Vec<BigUint>,
}

impl Dist<usize> for HeadcountDist {
    fn solve(n: usize) -> Self {
        let mut data = Vec::with_capacity(n + 1);
        let mut c = BigUint::from(1u32);
        for k in 0..=n {
            data.push(c.clone());
            if k < n {
                c *= BigUint::from(n as u32 - k as u32);
                c /= BigUint::from(k as u32 + 1);
            }
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

impl Statistic<CoinGame, HeadcountDist, usize> for Headcount {
    fn eval(seq: &[usize]) -> usize {
        seq.iter().sum()
    }
}

#[cfg(test)]
mod tests {
    use crate::games::validate_with;

    use super::*;

    #[test]
    fn test_headcount() {
        (1..=10).for_each(|n| validate_with::<Headcount, _, _, _>(n));
    }
}

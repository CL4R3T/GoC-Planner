use num_bigint::BigUint;

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
}

impl GameFormula for CoinFormula {
    fn all() -> Vec<Self> {
        vec![
            CoinFormula::AtLeastX,
            CoinFormula::ExactX,
            CoinFormula::LongestStreak,
        ]
    }

    fn freqs(&self, n: usize) -> Vec<BigUint> {
        match self {
            CoinFormula::ExactX => Headcount::dist(n).all_freqs(),
            CoinFormula::AtLeastX => tail_sums(Headcount::dist(n).all_freqs()),
            CoinFormula::LongestStreak => tail_sums(LongestStreak::dist(n).all_freqs()),
        }
    }

    fn mode(&self) -> Mode {
        match self {
            CoinFormula::AtLeastX | CoinFormula::LongestStreak => Mode::AtLeast,
            CoinFormula::ExactX => Mode::Exact,
        }
    }
}

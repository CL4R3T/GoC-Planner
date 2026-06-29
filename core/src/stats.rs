pub fn expected_attempts(p: f64) -> f64 {
    if p > 0.0 { 1.0 / p } else { f64::INFINITY }
}

pub fn pity99(p: f64) -> usize {
    if p <= 0.0 {
        return usize::MAX;
    }
    if p >= 0.99 {
        return 1;
    }
    (0.01f64.ln() / (1.0 - p).ln()).ceil() as usize
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn expected_and_pity() {
        assert_eq!(expected_attempts(0.0), f64::INFINITY);
        assert!((expected_attempts(0.25) - 4.0).abs() < 1e-12);
        assert_eq!(pity99(0.0), usize::MAX);
        assert_eq!(pity99(0.99), 1);
        assert_eq!(pity99(1.0), 1);
        assert!(pity99(0.5) >= 7 && pity99(0.5) <= 7);
    }
}

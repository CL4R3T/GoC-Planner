"""Fair coin (k=2) formulas, in unlock order."""

from functools import lru_cache
from math import isqrt

from generators.base import Formula
from core.utils import binom

K = 2


@lru_cache(maxsize=None)
def _primes_upto(n: int) -> list[int]:
    """Cached list of primes in [2, n] using Sieve of Eratosthenes."""
    if n < 2:
        return []
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, isqrt(n) + 1):
        if sieve[i]:
            step = i
            start = i * i
            sieve[start:n + 1:step] = [False] * ((n - start) // step + 1)
    return [i for i, ok in enumerate(sieve) if ok]


def _at_least_x_heads(n: int, x: int) -> int:
    """Favorable outcomes with at least x heads in n flips: sum_{i=x}^{n} C(n,i)."""
    return sum(binom(n, i) for i in range(x, n + 1))


def _exact_x_heads(n: int, x: int) -> int:
    """Favorable outcomes with exactly x heads in n flips: C(n,x)."""
    return binom(n, x)


@lru_cache(maxsize=None)
def _no_streak(n: int, x: int) -> int:
    """Sequences of length n with NO run of x consecutive heads.

    Recurrence: a_n = a_{n-1} + ... + a_{n-x}  for n >= x.
    Base: a_n = 2^n for n < x.
    """
    if n < x:
        return 2 ** n
    total = 0
    for i in range(1, x + 1):
        total += _no_streak(n - i, x)
    return total


def _longest_streak(n: int, x: int) -> int:
    """Favorable outcomes with at least x consecutive heads."""
    if x > n:
        return 0
    return (2 ** n) - _no_streak(n, x)


def _longest_alternating(n: int, x: int) -> int:
    """Favorable outcomes containing a length-x perfectly alternating substring.

    An alternating substring of length x means x-1 consecutive alternations
    (differences) in a row. The difference sequence of length n-1 is itself
    n-1 independent fair coin flips. So this reduces to:
        2 * (sequences of length n-1 with a run of x-1 consecutive 1's)
    i.e. 2 * LongestStreak(n-1, x-1).
    """
    if x <= 1:
        return 2 ** n
    if x > n:
        return 0
    return 2 * _longest_streak(n - 1, x - 1)


FORMULAS: list[Formula] = [
    Formula(
        name="At Least X",
        kind="cumulative",
        valid_x=lambda n: list(range(1, n + 1)),
        compute=_at_least_x_heads,
    ),
    Formula(
        name="Exact Count",
        kind="exact",
        valid_x=lambda n: list(range(1, n + 1)),
        compute=_exact_x_heads,
    ),
    Formula(
        name="Longest Streak",
        kind="cumulative",
        valid_x=lambda n: list(range(1, n + 1)),
        compute=_longest_streak,
    ),
    Formula(
        name="Alternating",
        kind="cumulative",
        valid_x=lambda n: list(range(2, n + 1)),
        compute=_longest_alternating,
    ),
    Formula(
        name="Prime Count",
        kind="binary",
        valid_x=lambda n: [0],  # placeholder, x is ignored
        compute=lambda n, x: sum(
            binom(n, p) for p in _primes_upto(n)
        ),
    ),
]

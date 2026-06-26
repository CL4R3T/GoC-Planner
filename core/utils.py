"""Combinatorics and fixed-point integer utilities."""

from functools import lru_cache


@lru_cache(maxsize=None)
def binom(n: int, k: int) -> int:
    """C(n, k) as exact Python int.

    Uses recurrence C(n,k) = C(n,k-1) * (n-k+1) // k, no floating point.
    Results are LRU-cached.
    """
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    if k > n - k:
        k = n - k
    result = 1
    for i in range(1, k + 1):
        result = result * (n - i + 1) // i
    return result



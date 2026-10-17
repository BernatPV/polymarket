"""Competitive-programming utilities: graph input reader, Fibonacci, binomial.

Functions:
- read_graph(): reads graph from stdin where first two ints are `n m` followed
  by `m` edges (u v) optionally with weight.
- binomial(n,k): returns C(n,k) (uses math.comb if available).
- fib(n): returns nth Fibonacci number (0-indexed) using fast-doubling.
"""
from typing import List, Tuple
import sys


def read_graph(undirected: bool = True, weighted: bool = False, one_based: bool = True) -> Tuple[int, List[List]]:
    """Read graph from stdin. Expected format:
    n m
    u v
    u v w  (if weighted=True)

    Returns (n, adjacency_list). If weighted, adjacency list stores (v,w),
    otherwise stores v.
    """
    data = sys.stdin.read().strip().split()
    if not data:
        return 0, []
    it = iter(map(int, data))
    n = next(it)
    m = next(it)
    adj = [[] for _ in range(n)]
    offset = 1 if one_based else 0
    for _ in range(m):
        u = next(it) - offset
        v = next(it) - offset
        if weighted:
            w = next(it)
            adj[u].append((v, w))
            if undirected:
                adj[v].append((u, w))
        else:
            adj[u].append(v)
            if undirected:
                adj[v].append(u)
    return n, adj


def binomial(n: int, k: int) -> int:
    """Compute C(n, k). Handles large n where Python's math.comb is available.
    Falls back to multiplicative formula.
    """
    if k < 0 or k > n:
        return 0
    try:
        from math import comb

        return comb(n, k)
    except Exception:
        k = min(k, n - k)
        res = 1
        for i in range(1, k + 1):
            res = res * (n - k + i) // i
        return res


def fib(n: int) -> int:
    """Return the n-th Fibonacci number (0-indexed) using fast doubling."""
    def _fd(x: int) -> Tuple[int, int]:
        if x == 0:
            return 0, 1
        a, b = _fd(x >> 1)
        c = a * (2 * b - a)
        d = a * a + b * b
        if x & 1:
            return d, c + d
        else:
            return c, d

    return _fd(n)[0]


if __name__ == "__main__":
    # Quick demo when run directly
    print("binomial(5,2)", binomial(5, 2))
    print("fib(10)", fib(10))
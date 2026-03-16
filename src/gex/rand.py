"""Seedable PRNG wrapper around Python's random.Random."""

import random


class SeededRandom:
    """Deterministic PRNG using Python's Mersenne Twister."""

    def __init__(self, seed: int):
        self._rng = random.Random(seed)

    def intn(self, n: int) -> int:
        """Returns a non-negative pseudo-random integer in [0, n)."""
        if n <= 0:
            raise ValueError("invalid argument to intn")
        return self._rng.randrange(n)

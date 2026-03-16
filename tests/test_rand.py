"""Tests for SeededRandom PRNG wrapper."""

import pytest

from gex.rand import SeededRandom


class TestSeededRandom:
    def test_deterministic(self):
        rng1 = SeededRandom(42)
        rng2 = SeededRandom(42)
        for _ in range(100):
            assert rng1.intn(1000) == rng2.intn(1000)

    def test_different_seeds_differ(self):
        rng1 = SeededRandom(1)
        rng2 = SeededRandom(2)
        vals1 = [rng1.intn(1000) for _ in range(10)]
        vals2 = [rng2.intn(1000) for _ in range(10)]
        assert vals1 != vals2


class TestIntn:
    def test_range(self):
        rng = SeededRandom(99)
        for n in [1, 2, 10, 100, 1000, (1 << 32)]:
            for _ in range(100):
                v = rng.intn(n)
                assert 0 <= v < n

    def test_n_equals_one_always_zero(self):
        rng = SeededRandom(42)
        for _ in range(100):
            assert rng.intn(1) == 0

    def test_invalid_raises(self):
        rng = SeededRandom(1)
        with pytest.raises(ValueError, match="invalid argument"):
            rng.intn(0)
        with pytest.raises(ValueError, match="invalid argument"):
            rng.intn(-1)

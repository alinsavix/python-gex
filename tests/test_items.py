"""Tests for item stamp definitions."""

import pytest

from gex.items import _tr, ITEM_STAMPS
from gex.roms import GexError


class TestTr:
    def test_basic_range(self):
        assert _tr(10, 4) == [10, 11, 12, 13]

    def test_single(self):
        assert _tr(5, 1) == [5]

    def test_hex_values(self):
        assert _tr(0xAFC, 4) == [0xAFC, 0xAFD, 0xAFE, 0xAFF]


class TestItemStamps:
    def test_all_items_have_required_fields(self):
        required = {"width", "numbers", "ptype", "pnum"}
        for name, info in ITEM_STAMPS.items():
            assert required.issubset(info.keys()), f"Item '{name}' missing fields"

    def test_numbers_length_matches_grid(self):
        for name, info in ITEM_STAMPS.items():
            w = info["width"]
            n = len(info["numbers"])
            assert n % w == 0, f"Item '{name}': {n} tiles not divisible by width {w}"

    def test_ptype_is_valid(self):
        from gex.palettes import GAUNTLET_PALETTES
        for name, info in ITEM_STAMPS.items():
            assert info["ptype"] in GAUNTLET_PALETTES, \
                f"Item '{name}' has invalid ptype '{info['ptype']}'"

    def test_known_items_exist(self):
        known = ["key", "food", "potion", "treasure", "ghost", "grunt",
                 "demon", "exit", "dragon", "blank"]
        for item in known:
            assert item in ITEM_STAMPS

    def test_item_count(self):
        assert len(ITEM_STAMPS) == 58

    def test_blank_is_zeros(self):
        assert ITEM_STAMPS["blank"]["numbers"] == [0, 0, 0, 0]

    def test_dragon_is_4x4(self):
        d = ITEM_STAMPS["dragon"]
        assert d["width"] == 4
        assert len(d["numbers"]) == 16

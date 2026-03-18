"""Tests for floor stamp logic."""

from gex.floor import floor_get_tiles, FLOOR_STAMPS, _FLOOR_ADJ_KEYWORDS


class TestFloorGetTiles:
    def test_basic_tiles(self):
        tiles = floor_get_tiles(0, 0)
        expected = [(0 * 48) + FLOOR_STAMPS[0][i] for i in range(4)]
        assert tiles == expected

    def test_returns_four_tiles(self):
        tiles = floor_get_tiles(3, 5)
        assert len(tiles) == 4

    def test_floor_num_offset(self):
        # Different floor nums should produce different tile ranges
        tiles_0 = floor_get_tiles(0, 0)
        tiles_1 = floor_get_tiles(1, 0)
        # floor_num * 48 is the offset
        assert tiles_1[0] - tiles_0[0] == 48

    def test_floor_adj_changes_stamps(self):
        tiles_a = floor_get_tiles(0, 0)
        tiles_b = floor_get_tiles(0, 1)
        assert tiles_a != tiles_b


class TestFloorStamps:
    def test_count(self):
        assert len(FLOOR_STAMPS) == 32

    def test_each_has_four_tiles(self):
        for i, stamp in enumerate(FLOOR_STAMPS):
            assert len(stamp) == 4, f"FLOOR_STAMPS[{i}] has {len(stamp)} tiles"


class TestFloorParsing:
    def test_floor_adj_hwall(self):
        assert _FLOOR_ADJ_KEYWORDS["hwall"] == 4

    def test_floor_adj_vwall(self):
        assert _FLOOR_ADJ_KEYWORDS["vwall"] == 16

    def test_floor_adj_dwall(self):
        assert _FLOOR_ADJ_KEYWORDS["dwall"] == 8

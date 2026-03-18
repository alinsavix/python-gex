"""Tests for wall stamp logic."""

from gex.wall import (
    WALL_STAMPS,
    SHRUB_STAMPS,
    SHRUB_DESTRUCT_STAMPS,
    FF_MAP,
    WALL_MAP,
    SHRUB_WALL_MAP,
    _WALL_ADJ_MAP,
)


class TestWallData:
    def test_wall_stamps_6_patterns(self):
        # 6 patterns * 68 stamps each = 408
        assert len(WALL_STAMPS) == 6 * 68

    def test_each_stamp_has_four_tiles(self):
        for i, stamp in enumerate(WALL_STAMPS):
            assert len(stamp) == 4, f"WALL_STAMPS[{i}] has {len(stamp)} tiles"

    def test_shrub_stamps_count(self):
        assert len(SHRUB_STAMPS) == 16

    def test_shrub_destruct_count(self):
        assert len(SHRUB_DESTRUCT_STAMPS) == 3

    def test_ff_map_count(self):
        assert len(FF_MAP) == 16

    def test_wall_map_size(self):
        assert len(WALL_MAP) == 256

    def test_shrub_wall_map_size(self):
        assert len(SHRUB_WALL_MAP) == 256


class TestWallParsing:
    def test_wall_adj_directions(self):
        for d in ["u", "ur", "r", "dr", "d", "dl", "l", "ul"]:
            assert d in _WALL_ADJ_MAP, f"Direction '{d}' should be in _WALL_ADJ_MAP"

    def test_wall_adj_no_match(self):
        assert "x" not in _WALL_ADJ_MAP
        assert "up" not in _WALL_ADJ_MAP

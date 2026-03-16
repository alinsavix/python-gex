"""Tests for wall stamp logic."""

from gex.wall import (
    WALL_STAMPS,
    SHRUB_STAMPS,
    SHRUB_DESTRUCT_STAMPS,
    FF_MAP,
    WALL_MAP,
    SHRUB_WALL_MAP,
    RE_WALL_NUM,
    RE_WALL_COLOR,
    RE_WALL_ADJ,
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


class TestWallRegexes:
    def test_wall_num(self):
        m = RE_WALL_NUM.match("wall3")
        assert m and m.group(1) == "3"

    def test_wall_num_no_match(self):
        assert RE_WALL_NUM.match("wall") is None
        assert RE_WALL_NUM.match("floor3") is None

    def test_wall_color(self):
        m = RE_WALL_COLOR.match("c5")
        assert m and m.group(1) == "5"

    def test_wall_adj_directions(self):
        for d in ["u", "ur", "r", "dr", "d", "dl", "l", "ul"]:
            m = RE_WALL_ADJ.match(d)
            assert m is not None, f"Direction '{d}' should match"
            assert m.group(1) == d

    def test_wall_adj_no_match(self):
        assert RE_WALL_ADJ.match("x") is None
        assert RE_WALL_ADJ.match("up") is None

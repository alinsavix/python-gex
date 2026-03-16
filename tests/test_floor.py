"""Tests for floor stamp logic."""

from gex.floor import floor_get_tiles, FLOOR_STAMPS, RE_FLOOR_NUM, RE_FLOOR_COLOR, RE_FLOOR_ADJ


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


class TestFloorRegexes:
    def test_floor_num_pattern(self):
        m = RE_FLOOR_NUM.match("floor5")
        assert m and m.group(1) == "5"

    def test_floor_num_no_match(self):
        assert RE_FLOOR_NUM.match("wall5") is None

    def test_floor_color_pattern(self):
        m = RE_FLOOR_COLOR.match("c12")
        assert m and m.group(1) == "12"

    def test_floor_adj_var(self):
        m = RE_FLOOR_ADJ.match("var3")
        assert m and m.group(1) == "3"

    def test_floor_adj_hwall(self):
        m = RE_FLOOR_ADJ.match("hwall")
        assert m and m.group(2) == "hwall"

    def test_floor_adj_vwall(self):
        m = RE_FLOOR_ADJ.match("vwall")
        assert m and m.group(3) == "vwall"

    def test_floor_adj_dwall(self):
        m = RE_FLOOR_ADJ.match("dwall")
        assert m and m.group(4) == "dwall"

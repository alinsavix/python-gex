"""Tests for door stamp logic."""

from gex.door import door_get_tiles, DOOR_STAMPS, DOOR_HORIZ, DOOR_VERT


class TestDoorConstants:
    def test_directions(self):
        assert DOOR_HORIZ == 0
        assert DOOR_VERT == 1

    def test_stamp_count(self):
        assert len(DOOR_STAMPS) == 16


class TestDoorGetTiles:
    def test_no_adjacency_returns_none(self):
        assert door_get_tiles(DOOR_HORIZ, 0) is None

    def test_up_only_returns_none(self):
        assert door_get_tiles(DOOR_HORIZ, 1) is None

    def test_valid_adjacency_returns_four_tiles(self):
        # adj=3 (up-right) has stamp 0x1D34
        tiles = door_get_tiles(DOOR_HORIZ, 3)
        assert tiles is not None
        assert len(tiles) == 4
        assert tiles == [0x1D34, 0x1D35, 0x1D36, 0x1D37]

    def test_all_adjacent(self):
        # adj=15 (all four) has stamp 0x1D28
        tiles = door_get_tiles(DOOR_HORIZ, 15)
        assert tiles is not None
        assert tiles[0] == 0x1D28

    def test_zero_stamps_return_none(self):
        for adj in range(16):
            if DOOR_STAMPS[adj] == 0:
                assert door_get_tiles(DOOR_HORIZ, adj) is None
            else:
                assert door_get_tiles(DOOR_HORIZ, adj) is not None

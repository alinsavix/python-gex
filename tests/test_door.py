"""Tests for door stamp logic."""

import pytest

from gex.door import door_get_tiles, DOOR_STAMPS, DOOR_HORIZ, DOOR_VERT
from gex.roms import GexError


class TestDoorConstants:
    def test_directions(self):
        assert DOOR_HORIZ == 0
        assert DOOR_VERT == 1

    def test_stamp_count(self):
        assert len(DOOR_STAMPS) == 16


class TestDoorGetTiles:
    def test_no_adjacency_raises(self):
        with pytest.raises(GexError):
            door_get_tiles(DOOR_HORIZ, 0)

    def test_up_only_raises(self):
        with pytest.raises(GexError):
            door_get_tiles(DOOR_HORIZ, 1)

    def test_valid_adjacency_returns_four_tiles(self):
        tiles = door_get_tiles(DOOR_HORIZ, 3)
        assert len(tiles) == 4
        assert tiles == [0x1D34, 0x1D35, 0x1D36, 0x1D37]

    def test_all_adjacent(self):
        tiles = door_get_tiles(DOOR_HORIZ, 15)
        assert tiles[0] == 0x1D28

    def test_zero_stamps_raise(self):
        for adj in range(16):
            if DOOR_STAMPS[adj] == 0:
                with pytest.raises(GexError):
                    door_get_tiles(DOOR_HORIZ, adj)
            else:
                tiles = door_get_tiles(DOOR_HORIZ, adj)
                assert tiles is not None

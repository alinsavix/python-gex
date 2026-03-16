"""Tests for maze decompression logic."""

import pytest

from gex.constants import MazeObjIds
from gex.mazedecode import index2xy, iswall, isspecialfloor, expand, vexpand, maze_decompress, Maze


class TestIndex2xy:
    def test_origin(self):
        assert index2xy(0) == (0, 0)

    def test_first_row(self):
        assert index2xy(5) == (5, 0)
        assert index2xy(31) == (31, 0)

    def test_second_row(self):
        assert index2xy(32) == (0, 1)
        assert index2xy(33) == (1, 1)

    def test_last_cell(self):
        assert index2xy(1023) == (31, 31)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="index < 0"):
            index2xy(-1)

    def test_arbitrary(self):
        # row 10, col 15 -> index = 10*32 + 15 = 335
        assert index2xy(335) == (15, 10)


class TestIswall:
    def test_regular_wall(self):
        assert iswall(MazeObjIds.WALL_REGULAR) is True

    def test_secret_wall(self):
        assert iswall(MazeObjIds.WALL_SECRET) is True

    def test_destructable_wall(self):
        assert iswall(MazeObjIds.WALL_DESTRUCTABLE) is True

    def test_random_wall(self):
        assert iswall(MazeObjIds.WALL_RANDOM) is True

    def test_trapcyc_walls(self):
        assert iswall(MazeObjIds.WALL_TRAPCYC1) is True
        assert iswall(MazeObjIds.WALL_TRAPCYC2) is True
        assert iswall(MazeObjIds.WALL_TRAPCYC3) is True

    def test_floor_is_not_wall(self):
        assert iswall(MazeObjIds.TILE_FLOOR) is False

    def test_door_is_not_wall(self):
        assert iswall(MazeObjIds.DOOR_HORIZ) is False

    def test_movable_wall_is_not_wall(self):
        assert iswall(MazeObjIds.WALL_MOVABLE) is False


class TestIsspecialfloor:
    def test_stun(self):
        assert isspecialfloor(MazeObjIds.TILE_STUN) is True

    def test_traps(self):
        assert isspecialfloor(MazeObjIds.TILE_TRAP1) is True
        assert isspecialfloor(MazeObjIds.TILE_TRAP2) is True
        assert isspecialfloor(MazeObjIds.TILE_TRAP3) is True

    def test_exit(self):
        assert isspecialfloor(MazeObjIds.EXIT) is True
        assert isspecialfloor(MazeObjIds.EXITTO6) is True

    def test_transporter(self):
        assert isspecialfloor(MazeObjIds.TRANSPORTER) is True

    def test_regular_floor_is_not_special(self):
        assert isspecialfloor(MazeObjIds.TILE_FLOOR) is False

    def test_wall_is_not_special_floor(self):
        assert isspecialfloor(MazeObjIds.WALL_REGULAR) is False


class TestExpand:
    def test_floor_skips_without_writing(self):
        maze = Maze()
        new_loc = expand(maze, 32, MazeObjIds.TILE_FLOOR, 5)
        assert new_loc == 37
        assert len(maze.data) == 0

    def test_wall_writes_cells(self):
        maze = Maze()
        new_loc = expand(maze, 32, MazeObjIds.WALL_REGULAR, 3)
        assert new_loc == 35
        assert maze.data[(0, 1)] == MazeObjIds.WALL_REGULAR
        assert maze.data[(1, 1)] == MazeObjIds.WALL_REGULAR
        assert maze.data[(2, 1)] == MazeObjIds.WALL_REGULAR

    def test_single_object(self):
        maze = Maze()
        new_loc = expand(maze, 64, MazeObjIds.KEY, 1)
        assert new_loc == 65
        assert maze.data[(0, 2)] == MazeObjIds.KEY

    def test_dragon_double_increments(self):
        maze = Maze()
        new_loc = expand(maze, 32, MazeObjIds.MONST_DRAGON, 4)
        assert new_loc == 36
        # Dragon uses double increment, so only writes at even positions
        assert maze.data[(0, 1)] == MazeObjIds.MONST_DRAGON
        assert maze.data[(2, 1)] == MazeObjIds.MONST_DRAGON
        assert (1, 1) not in maze.data


class TestVexpand:
    def test_floor_skips(self):
        maze = Maze()
        new_loc = vexpand(maze, 64, MazeObjIds.TILE_FLOOR, 3)
        assert new_loc == 65
        assert len(maze.data) == 0

    def test_vertical_expansion(self):
        maze = Maze()
        # At location 96 (row 3, col 0), expand 3 upward
        new_loc = vexpand(maze, 96, MazeObjIds.WALL_REGULAR, 3)
        assert new_loc == 97
        # Should write at location, location-32, location-64
        assert maze.data[(0, 3)] == MazeObjIds.WALL_REGULAR
        assert maze.data[(0, 2)] == MazeObjIds.WALL_REGULAR
        assert maze.data[(0, 1)] == MazeObjIds.WALL_REGULAR


class TestMazeDecompress:
    def _minimal_compressed(self, secret=0, flags=0, wallpat=0, floorpat=0,
                            wallcol=0, floorcol=0, body=None):
        """Build a minimal compressed maze byte sequence."""
        if body is None:
            # Fill with floor tiles then terminator
            # 0xC0 | 0x1F = floor for 32 tiles, repeat enough to fill 31 rows (992 cells)
            body = []
            remaining = 992  # 32*32 - 32 (first row is auto-filled)
            while remaining > 0:
                chunk = min(remaining, 32)
                body.append(0xC0 | (chunk - 1))
                remaining -= chunk
            body.append(0)  # terminator

        data = [
            secret & 0x1F,
            (flags >> 24) & 0xFF,
            (flags >> 16) & 0xFF,
            (flags >> 8) & 0xFF,
            flags & 0xFF,
            (floorpat << 4) | wallpat,
            (floorcol << 4) | wallcol,
            0, 0, 0, 0,  # htype1, htype2, vtype1, vtype2
        ] + body
        return data

    def test_metadata_parsing(self):
        data = self._minimal_compressed(secret=5, wallpat=3, floorpat=7,
                                         wallcol=2, floorcol=9)
        maze = maze_decompress(data, metaonly=True)
        assert maze.secret == 5
        assert maze.wallpattern == 3
        assert maze.floorpattern == 7
        assert maze.wallcolor == 2
        assert maze.floorcolor == 9

    def test_flags_big_endian(self):
        flags = 0x12345678
        data = self._minimal_compressed(flags=flags)
        maze = maze_decompress(data, metaonly=True)
        assert maze.flags == flags

    def test_first_row_all_walls(self):
        data = self._minimal_compressed()
        maze = maze_decompress(data)
        for x in range(32):
            assert maze.data[(x, 0)] == MazeObjIds.WALL_REGULAR

    def test_literal_object_placement(self):
        # Place a KEY (53 = 0x35) as a literal at position 32 (first cell after wall row)
        body = [MazeObjIds.KEY]
        remaining = 991
        while remaining > 0:
            chunk = min(remaining, 32)
            body.append(0xC0 | (chunk - 1))
            remaining -= chunk
        body.append(0)
        data = self._minimal_compressed(body=body)
        maze = maze_decompress(data)
        assert maze.data[(0, 1)] == MazeObjIds.KEY

    def test_encodedbytes_set(self):
        data = self._minimal_compressed()
        maze = maze_decompress(data)
        assert maze.encodedbytes == len(data)


class TestMazeDataclass:
    def test_defaults(self):
        m = Maze()
        assert m.data == {}
        assert m.encodedbytes == 0
        assert m.secret == 0
        assert m.flags == 0
        assert m.wallpattern == 0
        assert m.wallcolor == 0
        assert m.floorpattern == 0
        assert m.floorcolor == 0

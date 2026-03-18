"""Tests for playfield rendering helpers (no ROM access needed)."""

import pytest
from PIL import Image

from gex.constants import MazeObjIds
from gex.mazedecode import Maze
from gex.pfrender import (
    whatis,
    isdoor,
    isforcefield,
    checkwalladj3,
    checkwalladj8,
    checkdooradj4,
    checkffadj4,
    copyedges,
    dotat,
    renderdots,
    ff_make_map,
)
from gex.palettes import IRGB


def _maze_with_data(data: dict) -> Maze:
    m = Maze()
    m.data = data
    return m


class TestWhatis:
    def test_returns_value(self):
        maze = _maze_with_data({(1, 2): MazeObjIds.KEY})
        assert whatis(maze, 1, 2) == MazeObjIds.KEY

    def test_missing_returns_zero(self):
        maze = _maze_with_data({})
        assert whatis(maze, 5, 5) == 0


class TestIsdoor:
    def test_horiz_door(self):
        assert isdoor(MazeObjIds.DOOR_HORIZ) is True

    def test_vert_door(self):
        assert isdoor(MazeObjIds.DOOR_VERT) is True

    def test_wall_not_door(self):
        assert isdoor(MazeObjIds.WALL_REGULAR) is False


class TestIsforcefield:
    def test_forcefield(self):
        assert isforcefield(MazeObjIds.FORCEFIELDHUB) is True

    def test_other(self):
        assert isforcefield(MazeObjIds.KEY) is False


class TestCheckwalladj3:
    def test_no_walls(self):
        maze = _maze_with_data({})
        assert checkwalladj3(maze, 5, 5) == 0

    def test_wall_left(self):
        maze = _maze_with_data({(4, 5): MazeObjIds.WALL_REGULAR})
        assert checkwalladj3(maze, 5, 5) == 4

    def test_wall_below(self):
        maze = _maze_with_data({(5, 6): MazeObjIds.WALL_REGULAR})
        assert checkwalladj3(maze, 5, 5) == 16

    def test_wall_diag(self):
        maze = _maze_with_data({(4, 6): MazeObjIds.WALL_REGULAR})
        assert checkwalladj3(maze, 5, 5) == 8

    def test_all_three(self):
        maze = _maze_with_data({
            (4, 5): MazeObjIds.WALL_REGULAR,
            (5, 6): MazeObjIds.WALL_REGULAR,
            (4, 6): MazeObjIds.WALL_REGULAR,
        })
        assert checkwalladj3(maze, 5, 5) == 4 + 16 + 8


class TestCheckwalladj8:
    def test_no_walls(self):
        maze = _maze_with_data({})
        assert checkwalladj8(maze, 5, 5) == 0

    def test_surrounded(self):
        data = {}
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                data[(5 + dx, 5 + dy)] = MazeObjIds.WALL_REGULAR
        maze = _maze_with_data(data)
        assert checkwalladj8(maze, 5, 5) == 0xFF

    def test_individual_positions(self):
        positions = [
            ((-1, -1), 0x01),
            ((0, -1), 0x02),
            ((1, -1), 0x04),
            ((-1, 0), 0x08),
            ((1, 0), 0x10),
            ((-1, 1), 0x20),
            ((0, 1), 0x40),
            ((1, 1), 0x80),
        ]
        for (dx, dy), expected in positions:
            maze = _maze_with_data({(5 + dx, 5 + dy): MazeObjIds.WALL_REGULAR})
            assert checkwalladj8(maze, 5, 5) == expected


class TestCheckdooradj4:
    def test_no_doors(self):
        maze = _maze_with_data({})
        assert checkdooradj4(maze, 5, 5) == 0

    def test_door_above(self):
        maze = _maze_with_data({(5, 4): MazeObjIds.DOOR_HORIZ})
        assert checkdooradj4(maze, 5, 5) == 0x01

    def test_door_right(self):
        maze = _maze_with_data({(6, 5): MazeObjIds.DOOR_VERT})
        assert checkdooradj4(maze, 5, 5) == 0x02

    def test_door_below(self):
        maze = _maze_with_data({(5, 6): MazeObjIds.DOOR_HORIZ})
        assert checkdooradj4(maze, 5, 5) == 0x04

    def test_door_left(self):
        maze = _maze_with_data({(4, 5): MazeObjIds.DOOR_VERT})
        assert checkdooradj4(maze, 5, 5) == 0x08


class TestCheckffadj4:
    def test_no_forcefields(self):
        maze = _maze_with_data({})
        assert checkffadj4(maze, 5, 5) == 0

    def test_forcefield_right_with_gap(self):
        maze = _maze_with_data({(8, 5): MazeObjIds.FORCEFIELDHUB})
        assert checkffadj4(maze, 5, 5) & 0x02

    def test_forcefield_blocked_by_wall(self):
        maze = _maze_with_data({
            (6, 5): MazeObjIds.WALL_REGULAR,
            (8, 5): MazeObjIds.FORCEFIELDHUB,
        })
        assert checkffadj4(maze, 5, 5) & 0x02 == 0

    def test_adjacent_forcefield_not_counted(self):
        # j starts at 1 and checks j > 1, so directly adjacent (j=1) doesn't count
        maze = _maze_with_data({(6, 5): MazeObjIds.FORCEFIELDHUB})
        assert checkffadj4(maze, 5, 5) == 0


class TestCopyedges:
    def test_copies_left_to_right_when_no_wrap_h(self):
        maze = _maze_with_data({(0, 5): MazeObjIds.WALL_REGULAR})
        maze.flags = 0  # no wrapping
        copyedges(maze)
        assert maze.data[(32, 5)] == MazeObjIds.WALL_REGULAR

    def test_no_copy_when_wrap_h(self):
        from gex.constants import LFLAG4_WRAP_H
        maze = _maze_with_data({(0, 5): MazeObjIds.WALL_REGULAR})
        maze.flags = LFLAG4_WRAP_H
        copyedges(maze)
        assert (32, 5) not in maze.data


class TestDotat:
    def test_places_white_pixels(self):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        dotat(img, 5, 5)
        pixels = img.load()
        expected = IRGB(0xFFFF).to_rgba()
        assert pixels[5, 5] == expected
        assert pixels[6, 5] == expected
        assert pixels[5, 6] == expected
        assert pixels[6, 6] == expected

    def test_clips_at_boundary(self):
        img = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
        # Should not raise
        dotat(img, 3, 3)
        pixels = img.load()
        assert pixels[3, 3] == IRGB(0xFFFF).to_rgba()


class TestRenderdots:
    def test_one_dot(self):
        img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        renderdots(img, 0, 0, 1)
        pixels = img.load()
        assert pixels[7, 7] == IRGB(0xFFFF).to_rgba()

    def test_zero_dots_noop(self):
        img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        renderdots(img, 0, 0, 0)
        pixels = img.load()
        # All should remain transparent
        for y in range(32):
            for x in range(32):
                assert pixels[x, y] == (0, 0, 0, 0)


class TestFfMakeMap:
    def test_empty_maze(self):
        maze = _maze_with_data({})
        ffmap = ff_make_map(maze)
        assert len(ffmap) == 0

    def test_paired_forcefields_mark_between(self):
        maze = _maze_with_data({
            (5, 5): MazeObjIds.FORCEFIELDHUB,
            (5, 10): MazeObjIds.FORCEFIELDHUB,
        })
        ffmap = ff_make_map(maze)
        # Should mark cells between (5,5) and (5,10) downward
        for y in range(6, 10):
            assert (5, y) in ffmap

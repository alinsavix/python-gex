"""Tests for the constants module."""

from gex.constants import (
    MazeObjIds,
    MAZE_FLAG_STRINGS,
    MAZE_SECRET_STRINGS,
    LFLAG1_ODDANGLE_GHOSTS,
    LFLAG4_WRAP_H,
    LFLAG4_WRAP_V,
    TRICK_NONE,
    TRICK_IT,
)


class TestMazeObjIds:
    def test_tile_floor_is_zero(self):
        assert MazeObjIds.TILE_FLOOR == 0

    def test_forcefieldhub_is_63(self):
        assert MazeObjIds.FORCEFIELDHUB == 63

    def test_all_values_unique(self):
        values = [m.value for m in MazeObjIds]
        assert len(values) == len(set(values))

    def test_wall_types_contiguous(self):
        assert MazeObjIds.WALL_REGULAR == 2
        assert MazeObjIds.WALL_MOVABLE == 3
        assert MazeObjIds.WALL_SECRET == 4
        assert MazeObjIds.WALL_DESTRUCTABLE == 5
        assert MazeObjIds.WALL_RANDOM == 6

    def test_is_intenum(self):
        # Can be used as an integer
        assert MazeObjIds.TILE_FLOOR + 1 == 1
        assert MazeObjIds.KEY == 53


class TestFlags:
    def test_flags_are_powers_of_two(self):
        for flag in MAZE_FLAG_STRINGS.keys():
            assert flag & (flag - 1) == 0, f"Flag {flag} is not a power of 2"

    def test_wrap_flags(self):
        assert LFLAG4_WRAP_V == 16
        assert LFLAG4_WRAP_H == 32

    def test_flag_strings_all_present(self):
        assert len(MAZE_FLAG_STRINGS) == 29


class TestSecretStrings:
    def test_trick_none(self):
        assert MAZE_SECRET_STRINGS[TRICK_NONE] == "No trick"

    def test_trick_it(self):
        assert MAZE_SECRET_STRINGS[TRICK_IT] == "IT Could Be Nice"

    def test_all_tricks_sequential(self):
        assert set(MAZE_SECRET_STRINGS.keys()) == set(range(0x12))

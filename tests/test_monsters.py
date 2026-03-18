"""Tests for monster data and rendering."""

import pytest
from unittest.mock import patch, MagicMock

from gex.monsters import (
    GHOST_ANIMS,
    MONSTERS,
    Monster,
    RE_MONSTER_TYPE,
    RE_MONSTER_ACTION,
    RE_MONSTER_DIR,
    domonster,
)


class TestGhostAnims:
    DIRECTIONS = ["up", "upright", "right", "downright", "down", "downleft", "left", "upleft"]

    def test_walk_has_all_directions(self):
        assert set(GHOST_ANIMS["walk"].keys()) == set(self.DIRECTIONS)

    def test_each_direction_has_four_frames(self):
        for direction, frames in GHOST_ANIMS["walk"].items():
            assert len(frames) == 4, f"Direction '{direction}' has {len(frames)} frames"

    def test_frame_values_are_positive_ints(self):
        for direction, frames in GHOST_ANIMS["walk"].items():
            for frame in frames:
                assert isinstance(frame, int) and frame > 0, \
                    f"Direction '{direction}' has invalid frame: {frame}"

    def test_down_first_frame(self):
        # Spot-check a known tile number from the ROM data
        assert GHOST_ANIMS["walk"]["down"][0] == 0x800

    def test_up_first_frame(self):
        assert GHOST_ANIMS["walk"]["up"][0] == 0x890


class TestMonsters:
    def test_ghost_exists(self):
        assert "ghost" in MONSTERS

    def test_ghost_is_monster_instance(self):
        assert isinstance(MONSTERS["ghost"], Monster)

    def test_ghost_dimensions(self):
        ghost = MONSTERS["ghost"]
        assert ghost.xsize == 3
        assert ghost.ysize == 3

    def test_ghost_palette(self):
        ghost = MONSTERS["ghost"]
        assert ghost.ptype == "base"
        assert ghost.pnum == 0

    def test_ghost_has_walk_anims(self):
        assert "walk" in MONSTERS["ghost"].anims

    def test_ghost_anims_are_ghost_anims(self):
        assert MONSTERS["ghost"].anims is GHOST_ANIMS


class TestMonsterRegexes:
    def test_monster_type_ghost(self):
        m = RE_MONSTER_TYPE.match("ghost")
        assert m is not None
        assert m.group(1) == "ghost"
        assert m.group(2) is None

    def test_monster_type_ghost_with_level(self):
        m = RE_MONSTER_TYPE.match("ghost3")
        assert m is not None
        assert m.group(1) == "ghost"
        assert m.group(2) == "3"

    def test_monster_type_no_match(self):
        assert RE_MONSTER_TYPE.match("grunt") is None
        assert RE_MONSTER_TYPE.match("") is None

    def test_monster_action_walk(self):
        m = RE_MONSTER_ACTION.match("walk")
        assert m is not None and m.group(1) == "walk"

    def test_monster_action_fight(self):
        m = RE_MONSTER_ACTION.match("fight")
        assert m is not None and m.group(1) == "fight"

    def test_monster_action_attack(self):
        m = RE_MONSTER_ACTION.match("attack")
        assert m is not None and m.group(1) == "attack"

    def test_monster_action_no_match(self):
        assert RE_MONSTER_ACTION.match("run") is None

    def test_monster_dir_all_eight(self):
        dirs = ["up", "upright", "right", "downright", "down", "downleft", "left", "upleft"]
        for d in dirs:
            m = RE_MONSTER_DIR.match(d)
            assert m is not None and m.group(1) == d, f"Direction '{d}' should match"

    def test_monster_dir_no_match(self):
        assert RE_MONSTER_DIR.match("north") is None
        assert RE_MONSTER_DIR.match("") is None


class TestDomonster:
    def _call(self, arg, animate=False, pal_type="base", pal_num=0):
        with patch("gex.monsters.gen_image", return_value=MagicMock()) as mock_gen:
            with patch("gex.monsters.save_to_png") as mock_save:
                result = domonster(arg, "out.png", pal_type, pal_num, animate)
        return result, mock_gen, mock_save

    def test_returns_pal_type_and_num(self):
        result, _, _ = self._call("ghost-walk-up")
        pal_type, pal_num = result
        assert pal_type == "base"

    def test_default_direction_is_up(self):
        result, mock_gen, _ = self._call("ghost-walk")
        # Should not raise; direction defaults to "up"
        mock_gen.assert_called_once()

    def test_animate_false_calls_gen_image(self):
        _, mock_gen, mock_save = self._call("ghost-walk-down", animate=False)
        mock_gen.assert_called_once()
        mock_save.assert_called_once()

    def test_animate_true_skips_gen_image(self):
        _, mock_gen, mock_save = self._call("ghost-walk-up", animate=True)
        mock_gen.assert_not_called()
        mock_save.assert_not_called()

    def test_level_affects_pal_num(self):
        result1, _, _ = self._call("ghost-walk-up")
        result2, _, _ = self._call("ghost2-walk-up")
        _, pnum1 = result1
        _, pnum2 = result2
        assert pnum2 != pnum1

    def test_unknown_monster_raises(self):
        with pytest.raises(KeyError):
            domonster("demon-walk-up", "out.png", "base", 0, False)

    def test_tile_number_used_for_image(self):
        """Verify the correct tile number is passed to gen_image."""
        with patch("gex.monsters.gen_image", return_value=MagicMock()) as mock_gen:
            with patch("gex.monsters.save_to_png"):
                domonster("ghost-walk-down", "out.png", "base", 0, False)
        call_args = mock_gen.call_args[0]
        # First arg is the tile number; down/frame0 should be 0x800
        assert call_args[0] == 0x800

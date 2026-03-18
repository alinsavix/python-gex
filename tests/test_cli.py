"""Tests for CLI argument parsing and dispatch."""

import pytest
from unittest.mock import patch, MagicMock

from gex.cli import parse_args, main, RunType


class TestParseArgs:
    def test_defaults(self):
        with patch("sys.argv", ["gex"]):
            opts, extra = parse_args()
        assert opts.tile == "0"
        assert opts.pt == "base"
        assert opts.pn == "0"
        assert opts.x == 2
        assert opts.y == 2
        assert opts.output == "output.png"
        assert opts.animate is False
        assert opts.verbose is False
        assert opts.args == []
        assert extra == []

    def test_tile_flag(self):
        with patch("sys.argv", ["gex", "-t", "1A2B"]):
            opts, _ = parse_args()
        assert opts.tile == "1A2B"

    def test_output_flag(self):
        with patch("sys.argv", ["gex", "-o", "my_output.png"]):
            opts, _ = parse_args()
        assert opts.output == "my_output.png"

    def test_animate_flag(self):
        with patch("sys.argv", ["gex", "-a"]):
            opts, _ = parse_args()
        assert opts.animate is True

    def test_verbose_flag(self):
        with patch("sys.argv", ["gex", "-v"]):
            opts, _ = parse_args()
        assert opts.verbose is True

    def test_palette_flags(self):
        with patch("sys.argv", ["gex", "--pt", "floor", "--pn", "3"]):
            opts, _ = parse_args()
        assert opts.pt == "floor"
        assert opts.pn == "3"

    def test_xy_dimensions(self):
        with patch("sys.argv", ["gex", "-x", "4", "-y", "3"]):
            opts, _ = parse_args()
        assert opts.x == 4
        assert opts.y == 3

    def test_positional_arg(self):
        with patch("sys.argv", ["gex", "maze0"]):
            opts, _ = parse_args()
        assert opts.args == ["maze0"]

    def test_extra_args_captured(self):
        with patch("sys.argv", ["gex", "floor", "extra_arg"]):
            opts, extra = parse_args()
        # argparse captures known positional args; extra may end up in opts.args or extra
        all_args = opts.args + extra
        assert "floor" in all_args


class TestRunTypeDetection:
    """Test that main() dispatches to the right RunType based on arg."""

    def _run_main(self, argv):
        with patch("sys.argv", argv):
            with pytest.raises(SystemExit) as exc_info:
                main()
        return exc_info

    def test_no_args_no_tile_exits(self):
        with patch("sys.argv", ["gex"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1

    def test_tile_only_calls_gen_image(self):
        mock_img = MagicMock()
        with patch("sys.argv", ["gex", "-t", "1", "-o", "out.png"]):
            with patch("gex.cli.gen_image", return_value=mock_img) as mock_gen:
                with patch("gex.cli.save_to_png") as mock_save:
                    main()
        mock_gen.assert_called_once_with(1, 2, 2, "base", 0)
        mock_save.assert_called_once_with("out.png", mock_img)

    def test_floor_dispatches_to_dofloor(self):
        with patch("sys.argv", ["gex", "floor5", "-o", "out.png"]):
            with patch("gex.floor.dofloor") as mock_do:
                main()
        mock_do.assert_called_once_with("floor5", "out.png")

    def test_wall_dispatches_to_dowall(self):
        with patch("sys.argv", ["gex", "wall3", "-o", "out.png"]):
            with patch("gex.wall.dowall") as mock_do:
                main()
        mock_do.assert_called_once_with("wall3", "out.png")

    def test_item_dispatches_to_doitem(self):
        with patch("sys.argv", ["gex", "item-key", "-o", "out.png"]):
            with patch("gex.items.doitem") as mock_do:
                main()
        mock_do.assert_called_once_with("item-key", "out.png")

    def test_monster_dispatches_to_domonster(self):
        with patch("sys.argv", ["gex", "ghost-walk-up", "-o", "out.png"]):
            with patch("gex.monsters.domonster") as mock_do:
                main()
        mock_do.assert_called_once_with("ghost-walk-up", "out.png", "base", 0, False)

    def test_maze_dispatches_to_domaze(self):
        with patch("sys.argv", ["gex", "maze0", "-o", "out.png"]):
            with patch("gex.maze.domaze") as mock_do:
                main()
        mock_do.assert_called_once_with("maze0", "out.png", False)

    def test_maze_verbose_flag_passed(self):
        with patch("sys.argv", ["gex", "maze0", "-v", "-o", "out.png"]):
            with patch("gex.maze.domaze") as mock_do:
                main()
        mock_do.assert_called_once_with("maze0", "out.png", True)

    def test_unknown_arg_no_tile_exits(self):
        with patch("sys.argv", ["gex", "unknown_thing"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1

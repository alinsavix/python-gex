"""Integration tests that require Gauntlet II ROM files on disk.

These tests exercise the full rendering pipeline: reading ROM data,
parsing tiles, building stamps, decompressing mazes, and generating images.

Run with:  uv run pytest tests/test_integration_roms.py -v

All tests are skipped automatically if the ROMs directory is not found.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from gex.roms import _rom_dir, TILE_ROMS

# ---------------------------------------------------------------------------
# Skip the entire module if ROMs are not available
# ---------------------------------------------------------------------------
_ROM_PATH = _rom_dir()
_ROMS_EXIST = _ROM_PATH.is_dir() and (_ROM_PATH / TILE_ROMS[0][0]).is_file()

pytestmark = pytest.mark.skipif(
    not _ROMS_EXIST,
    reason=f"ROM files not found at {_ROM_PATH}",
)


@pytest.fixture
def tmp_png(tmp_path):
    """Return a temporary PNG file path that is cleaned up automatically."""
    return str(tmp_path / "output.png")


# ===================================================================
# ROM reading
# ===================================================================

class TestRomSplitRead:
    def test_read_tile_rom_bytes(self):
        from gex.roms import rom_split_read, SLAPSTIC_ROMS
        data = rom_split_read(SLAPSTIC_ROMS, 0, 16)
        assert isinstance(data, bytes)
        assert len(data) == 16

    def test_read_code_rom_bytes(self):
        from gex.roms import coderom_get_bytes, CODE_ROM_START
        data = coderom_get_bytes(CODE_ROM_START, 32)
        assert isinstance(data, bytes)
        assert len(data) == 32

    def test_slapstic_read_bytes(self):
        from gex.roms import slapstic_read_bytes
        data = slapstic_read_bytes(0, 64)
        assert isinstance(data, bytes)
        assert len(data) == 64


# ===================================================================
# Tile data reading and parsing
# ===================================================================

class TestTileReading:
    def test_get_tile_data_from_file(self):
        from gex.render import get_tile_data_from_file
        data = get_tile_data_from_file(TILE_ROMS[0][0], 0)
        assert isinstance(data, bytes)
        assert len(data) == 8

    def test_get_parsed_tile(self):
        from gex.render import get_parsed_tile
        tile = get_parsed_tile(0)
        assert len(tile) == 8
        for line in tile:
            assert len(line) == 8
            for pixel in line:
                assert 0 <= pixel <= 15

    def test_parsed_tile_various_banks(self):
        """Parse tiles from different ROM banks."""
        from gex.render import get_parsed_tile
        for tilenum in [0, 0x100, 0x800, 0x1000, 0x1800, 0x2000]:
            tile = get_parsed_tile(tilenum)
            assert len(tile) == 8

    def test_some_tiles_have_content(self):
        """At least some tiles in the ROM should contain non-zero pixel values."""
        from gex.render import get_parsed_tile
        # Check a range of tiles; at least one should have content
        found_content = False
        for tilenum in [0x11, 0x100, 0x1C1, 0x800, 0x801, 0x802]:
            tile = get_parsed_tile(tilenum)
            if any(pixel != 0 for line in tile for pixel in line):
                found_content = True
                break
        assert found_content, "No non-zero tiles found in ROM data"


# ===================================================================
# Single tile rendering
# ===================================================================

class TestTileRendering:
    def test_gen_image_single_tile(self):
        from gex.render import gen_image
        img = gen_image(0x100, 1, 1)
        assert img.size == (8, 8)
        assert img.mode == "RGBA"

    def test_gen_image_2x2(self):
        from gex.render import gen_image
        img = gen_image(0x100, 2, 2)
        assert img.size == (16, 16)

    def test_gen_image_with_palette(self):
        from gex.render import gen_image
        for ptype in ["base", "floor", "wall"]:
            img = gen_image(0x100, 2, 2, ptype, 0)
            assert img.size == (16, 16)

    def test_gen_image_from_array(self):
        from gex.render import gen_image_from_array
        tiles = [0x100, 0x101, 0x102, 0x103]
        img = gen_image_from_array(tiles, 2, 2)
        assert img.size == (16, 16)

    def test_save_to_png(self, tmp_png):
        from gex.render import gen_image, save_to_png
        img = gen_image(0x100, 2, 2)
        save_to_png(tmp_png, img)
        assert os.path.isfile(tmp_png)
        # Verify it's a valid PNG
        loaded = Image.open(tmp_png)
        assert loaded.size == (16, 16)


# ===================================================================
# Stamp system
# ===================================================================

class TestStampSystem:
    def test_fill_stamp(self):
        from gex.render import Stamp, fill_stamp
        stamp = Stamp(width=2, numbers=[0x100, 0x101, 0x102, 0x103],
                      ptype="base", pnum=0)
        fill_stamp(stamp)
        assert len(stamp.data) == 4
        for tile in stamp.data:
            assert len(tile) == 8

    def test_gen_stamp_from_array(self):
        from gex.render import gen_stamp_from_array
        stamp = gen_stamp_from_array([0x100, 0x101, 0x102, 0x103], 2, "base", 0)
        assert stamp.width == 2
        assert len(stamp.data) == 4

    def test_write_stamp_to_image(self):
        from gex.render import gen_stamp_from_array, write_stamp_to_image, blank_image
        stamp = gen_stamp_from_array([0x100, 0x101, 0x102, 0x103], 2, "base", 0)
        img = blank_image(16, 16)
        write_stamp_to_image(img, stamp, 0, 0)
        # Verify some pixels were written (not all transparent)
        pixels = img.load()
        has_content = any(
            pixels[x, y][3] > 0
            for x in range(16)
            for y in range(16)
        )
        assert has_content


# ===================================================================
# Floor rendering
# ===================================================================

class TestFloorRendering:
    def test_floor_get_stamp(self):
        from gex.floor import floor_get_stamp
        stamp = floor_get_stamp(0, 0, 0)
        assert stamp.width == 2
        assert len(stamp.data) == 4
        assert stamp.ptype == "floor"

    def test_floor_all_patterns(self):
        from gex.floor import floor_get_stamp
        for pattern in range(9):
            for adj in range(4):
                stamp = floor_get_stamp(pattern, adj, 0)
                assert len(stamp.data) == 4

    def test_floor_all_colors(self):
        from gex.floor import floor_get_stamp
        for color in range(16):
            stamp = floor_get_stamp(0, 0, color)
            assert stamp.pnum == color

    def test_dofloor_produces_image(self, tmp_png):
        from gex.floor import dofloor
        dofloor("floor0-c0-var0", tmp_png)
        assert os.path.isfile(tmp_png)
        img = Image.open(tmp_png)
        assert img.size == (16, 16)


# ===================================================================
# Wall rendering
# ===================================================================

class TestWallRendering:
    def test_wall_get_stamp_basic(self):
        from gex.wall import wall_get_stamp
        stamp = wall_get_stamp(0, 0, 0)
        assert stamp.width == 2
        assert len(stamp.data) == 4
        assert stamp.ptype == "wall"

    def test_wall_patterns_0_through_5(self):
        from gex.wall import wall_get_stamp
        for pattern in range(6):
            stamp = wall_get_stamp(pattern, 0, 0)
            assert stamp.ptype == "wall"

    def test_wall_shrub_patterns(self):
        from gex.wall import wall_get_stamp
        for pattern in [6, 7, 8, 9, 10, 11, 12]:
            stamp = wall_get_stamp(pattern, 0, 0)
            assert stamp.ptype == "shrub"

    def test_wall_destructable(self):
        from gex.wall import wall_get_destructable_stamp
        stamp = wall_get_destructable_stamp(0, 0, 0)
        assert stamp.width == 2
        assert len(stamp.data) == 4

    def test_wall_destructable_shrub(self):
        from gex.wall import wall_get_destructable_stamp
        stamp = wall_get_destructable_stamp(6, 0, 0)
        assert stamp.ptype == "shrub"

    def test_ff_get_stamp(self):
        from gex.wall import ff_get_stamp
        for adj in range(16):
            stamp = ff_get_stamp(adj)
            assert stamp.width == 2
            assert stamp.ptype == "teleff"

    def test_dowall_produces_image(self, tmp_png):
        from gex.wall import dowall
        dowall("wall0-c0-u-r", tmp_png)
        assert os.path.isfile(tmp_png)
        img = Image.open(tmp_png)
        assert img.size == (16, 16)


# ===================================================================
# Item rendering
# ===================================================================

class TestItemRendering:
    def test_item_get_stamp_key(self):
        from gex.items import item_get_stamp
        stamp = item_get_stamp("key")
        assert stamp.width == 2
        assert len(stamp.data) == 4
        assert stamp.trans0 is True

    def test_item_get_stamp_all_items(self):
        from gex.items import item_get_stamp, ITEM_STAMPS
        for name in ITEM_STAMPS:
            stamp = item_get_stamp(name)
            assert len(stamp.data) > 0, f"Item '{name}' has no tile data"

    def test_item_get_stamp_invalid_raises(self):
        from gex.items import item_get_stamp
        from gex.roms import GexError
        with pytest.raises(GexError, match="requested bad item"):
            item_get_stamp("nonexistent_item")

    def test_item_dragon_4x4(self):
        from gex.items import item_get_stamp
        stamp = item_get_stamp("dragon")
        assert stamp.width == 4
        assert len(stamp.data) == 16

    def test_doitem_produces_image(self, tmp_png):
        from gex.items import doitem
        doitem("item-key", tmp_png)
        assert os.path.isfile(tmp_png)
        img = Image.open(tmp_png)
        assert img.size == (16, 16)


# ===================================================================
# Door rendering
# ===================================================================

class TestDoorRendering:
    def test_door_get_stamp_with_adjacency(self):
        from gex.door import door_get_stamp, DOOR_HORIZ, DOOR_VERT
        # adj=3 has a real stamp
        stamp = door_get_stamp(DOOR_HORIZ, 3)
        assert stamp.width == 2
        assert stamp.trans0 is True
        assert len(stamp.data) == 4

    def test_door_get_stamp_fallback_horiz(self):
        from gex.door import door_get_stamp, DOOR_HORIZ
        # adj=0 has no custom stamp, falls back to hdoor item
        stamp = door_get_stamp(DOOR_HORIZ, 0)
        assert stamp.width == 2
        assert len(stamp.data) == 4

    def test_door_get_stamp_fallback_vert(self):
        from gex.door import door_get_stamp, DOOR_VERT
        stamp = door_get_stamp(DOOR_VERT, 0)
        assert stamp.width == 2
        assert len(stamp.data) == 4

    def test_all_adjacencies(self):
        from gex.door import door_get_stamp, DOOR_HORIZ
        for adj in range(16):
            stamp = door_get_stamp(DOOR_HORIZ, adj)
            assert stamp.width == 2


# ===================================================================
# Monster rendering
# ===================================================================

class TestMonsterRendering:
    def test_domonster_ghost_static(self, tmp_png):
        from gex.monsters import domonster
        ptype, pnum = domonster("ghost-walk-up", tmp_png, "base", 0, False)
        assert ptype == "base"
        assert pnum > 0
        assert os.path.isfile(tmp_png)
        img = Image.open(tmp_png)
        assert img.size == (24, 24)  # 3x3 tiles * 8

    def test_domonster_ghost_directions(self, tmp_png):
        from gex.monsters import domonster
        directions = ["up", "upright", "right", "downright",
                      "down", "downleft", "left", "upleft"]
        for d in directions:
            ptype, pnum = domonster(f"ghost-walk-{d}", tmp_png, "base", 0, False)
            assert os.path.isfile(tmp_png)

    def test_domonster_ghost_animate_no_file(self, tmp_png):
        from gex.monsters import domonster
        # animate=True skips file generation
        ptype, pnum = domonster("ghost-walk-up", tmp_png, "base", 0, True)
        assert ptype == "base"
        assert not os.path.isfile(tmp_png)

    def test_domonster_level(self, tmp_png):
        from gex.monsters import domonster
        # ghost2 -> level=2, pnum = base_pnum + (2+1) = 3
        ptype, pnum = domonster("ghost2-walk-up", tmp_png, "base", 0, False)
        assert pnum == 3  # pnum = 0 + (2+1)


# ===================================================================
# Maze decompression from ROM
# ===================================================================

class TestMazeFromRom:
    def test_read_maze_0(self):
        from gex.roms import slapstic_read_maze
        data = slapstic_read_maze(0)
        assert isinstance(data, list)
        assert len(data) > 11  # header + at least some body
        assert data[-1] == 0  # terminator

    def test_read_all_mazes(self):
        from gex.roms import slapstic_read_maze
        for i in range(117):
            data = slapstic_read_maze(i)
            assert len(data) > 11
            assert data[-1] == 0

    def test_decompress_maze_0(self):
        from gex.roms import slapstic_read_maze
        from gex.mazedecode import maze_decompress, MazeObjIds
        data = slapstic_read_maze(0)
        maze = maze_decompress(data)
        # First row should be all walls
        for x in range(32):
            assert maze.data[(x, 0)] == MazeObjIds.WALL_REGULAR
        # Should have metadata filled
        assert 0 <= maze.wallpattern <= 15
        assert 0 <= maze.floorpattern <= 15
        assert 0 <= maze.wallcolor <= 15
        assert 0 <= maze.floorcolor <= 15

    def test_decompress_maze_metadata_only(self):
        from gex.roms import slapstic_read_maze
        from gex.mazedecode import maze_decompress
        data = slapstic_read_maze(0)
        maze = maze_decompress(data, metaonly=True)
        # Metadata should be set but no map data
        assert maze.encodedbytes > 0
        assert len(maze.data) == 0

    def test_decompress_various_mazes(self):
        from gex.roms import slapstic_read_maze
        from gex.mazedecode import maze_decompress
        for maze_num in [0, 10, 50, 100, 116]:
            data = slapstic_read_maze(maze_num)
            maze = maze_decompress(data)
            # Every decompressed maze should have the first row as walls
            for x in range(32):
                assert maze.data[(x, 0)] == 2  # WALL_REGULAR

    def test_maze_secret_in_range(self):
        from gex.roms import slapstic_read_maze
        from gex.mazedecode import maze_decompress
        for maze_num in range(117):
            data = slapstic_read_maze(maze_num)
            maze = maze_decompress(data, metaonly=True)
            assert 0 <= maze.secret <= 0x1F


# ===================================================================
# Full maze image rendering
# ===================================================================

class TestMazeRendering:
    def test_domaze_meta_only(self, tmp_png, capsys):
        from gex.maze import domaze
        domaze("maze0-meta", tmp_png, False)
        captured = capsys.readouterr()
        assert "Maze number: 0" in captured.out
        assert "Wall pattern:" in captured.out
        assert not os.path.isfile(tmp_png)

    def test_domaze_full_render(self, tmp_png):
        from gex.maze import domaze
        domaze("maze0", tmp_png, False)
        assert os.path.isfile(tmp_png)
        img = Image.open(tmp_png)
        # Maze images are 32 tiles * 16px + 32px border + optional wrap space
        assert img.width >= 32 * 16 + 32
        assert img.height >= 32 * 16 + 32

    def test_domaze_verbose(self, tmp_png, capsys):
        from gex.maze import domaze
        domaze("maze0", tmp_png, True)
        captured = capsys.readouterr()
        assert "Wall pattern:" in captured.out
        assert os.path.isfile(tmp_png)

    def test_domaze_various_mazes(self, tmp_png):
        """Render a sample of mazes to verify no crashes."""
        from gex.maze import domaze
        for maze_num in [0, 5, 20, 50, 100]:
            domaze(f"maze{maze_num}", tmp_png, False)
            assert os.path.isfile(tmp_png)
            img = Image.open(tmp_png)
            assert img.width > 0 and img.height > 0


# ===================================================================
# Playfield rendering internals
# ===================================================================

class TestPlayfieldRendering:
    def test_genpfimage(self, tmp_png):
        from gex.roms import slapstic_read_maze
        from gex.mazedecode import maze_decompress
        from gex.pfrender import genpfimage
        data = slapstic_read_maze(0)
        maze = maze_decompress(data)
        genpfimage(maze, tmp_png)
        assert os.path.isfile(tmp_png)
        img = Image.open(tmp_png)
        assert img.mode == "RGBA"

    def test_genpfimage_wrapping_maze(self, tmp_png):
        """Find and render a maze with wrap flags to exercise arrow rendering."""
        from gex.constants import LFLAG4_WRAP_H, LFLAG4_WRAP_V
        from gex.roms import slapstic_read_maze
        from gex.mazedecode import maze_decompress
        from gex.pfrender import genpfimage
        # Search for a maze with wrapping
        for maze_num in range(117):
            data = slapstic_read_maze(maze_num)
            maze = maze_decompress(data)
            if maze.flags & (LFLAG4_WRAP_H | LFLAG4_WRAP_V):
                genpfimage(maze, tmp_png)
                assert os.path.isfile(tmp_png)
                img = Image.open(tmp_png)
                assert img.width > 0
                return
        pytest.skip("No wrapping mazes found in ROM set")


# ===================================================================
# CLI entry point
# ===================================================================

class TestCLI:
    def test_parse_args_defaults(self):
        from gex.cli import parse_args
        import sys
        old_argv = sys.argv
        sys.argv = ["gex"]
        try:
            opts, extra = parse_args()
            assert opts.output == "output.png"
            assert opts.x == 2
            assert opts.y == 2
            assert opts.pt == "base"
        finally:
            sys.argv = old_argv

    def test_parse_args_with_maze(self):
        import sys
        from gex.cli import parse_args
        old_argv = sys.argv
        sys.argv = ["gex", "-o", "test.png", "maze0"]
        try:
            opts, extra = parse_args()
            assert opts.output == "test.png"
            assert opts.args == ["maze0"]
        finally:
            sys.argv = old_argv


# ===================================================================
# Slapstic bank mapping
# ===================================================================

class TestSlapsticIntegration:
    def test_maze_addr_resolution(self):
        from gex.roms import slapstic_maze_get_real_addr
        for i in range(117):
            addr = slapstic_maze_get_real_addr(i)
            assert addr >= 0

    def test_maze_offset_readable(self):
        from gex.roms import slapstic_read_maze_offset
        offset = slapstic_read_maze_offset(0)
        assert isinstance(offset, int)
        assert offset >= 0


# ===================================================================
# End-to-end rendering of every object type
# ===================================================================

class TestEndToEndObjectRendering:
    """Render one stamp of each major object type to verify the full pipeline."""

    def test_render_floor_stamp_to_image(self, tmp_png):
        from gex.floor import floor_get_stamp
        from gex.render import blank_image, write_stamp_to_image, save_to_png
        stamp = floor_get_stamp(0, 0, 0)
        img = blank_image(16, 16)
        write_stamp_to_image(img, stamp, 0, 0)
        save_to_png(tmp_png, img)
        loaded = Image.open(tmp_png)
        assert loaded.size == (16, 16)

    def test_render_wall_stamp_to_image(self, tmp_png):
        from gex.wall import wall_get_stamp
        from gex.render import blank_image, write_stamp_to_image, save_to_png
        stamp = wall_get_stamp(0, 0xFF, 0)  # all adjacency bits
        img = blank_image(16, 16)
        write_stamp_to_image(img, stamp, 0, 0)
        save_to_png(tmp_png, img)
        loaded = Image.open(tmp_png)
        assert loaded.size == (16, 16)

    def test_render_item_stamps(self, tmp_png):
        from gex.items import item_get_stamp
        from gex.render import blank_image, write_stamp_to_image, save_to_png
        for name in ["key", "food", "potion", "treasure", "dragon", "tport"]:
            stamp = item_get_stamp(name)
            h = len(stamp.data) // stamp.width
            img = blank_image(stamp.width * 8, h * 8)
            write_stamp_to_image(img, stamp, 0, 0)
            save_to_png(tmp_png, img)
            loaded = Image.open(tmp_png)
            assert loaded.width > 0

    def test_render_door_stamp(self, tmp_png):
        from gex.door import door_get_stamp, DOOR_HORIZ
        from gex.render import blank_image, write_stamp_to_image, save_to_png
        stamp = door_get_stamp(DOOR_HORIZ, 15)
        img = blank_image(16, 16)
        write_stamp_to_image(img, stamp, 0, 0)
        save_to_png(tmp_png, img)
        assert os.path.isfile(tmp_png)

    def test_render_forcefield_stamp(self, tmp_png):
        from gex.wall import ff_get_stamp
        from gex.render import blank_image, write_stamp_to_image, save_to_png
        stamp = ff_get_stamp(0x0F)
        img = blank_image(16, 16)
        write_stamp_to_image(img, stamp, 0, 0)
        save_to_png(tmp_png, img)
        assert os.path.isfile(tmp_png)

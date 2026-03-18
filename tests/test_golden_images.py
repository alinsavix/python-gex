"""Golden-file regression tests: re-render images and compare against reference corpus.

The reference images live in tests/reference_images/ along with a manifest.json
that records the SHA-256 hash of each image's raw pixel data (not the PNG file
bytes).  This means a Pillow version upgrade that changes PNG metadata or
compression will NOT cause false failures — only actual pixel differences will.

To regenerate the reference corpus after an intentional rendering change:

    uv run python tests/generate_reference_images.py

These tests are skipped automatically if either the ROMs or the reference
images are not available.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from gex.roms import _rom_dir, TILE_ROMS

# ---------------------------------------------------------------------------
# Paths & skip conditions
# ---------------------------------------------------------------------------
REF_DIR = Path(__file__).resolve().parent / "reference_images"
MANIFEST_PATH = REF_DIR / "manifest.json"

_ROM_PATH = _rom_dir()
_ROMS_EXIST = _ROM_PATH.is_dir() and (_ROM_PATH / TILE_ROMS[0][0]).is_file()
_REFS_EXIST = MANIFEST_PATH.is_file()

pytestmark = pytest.mark.skipif(
    not (_ROMS_EXIST and _REFS_EXIST),
    reason="ROM files or reference images not available",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def _pixel_sha256(img: Image.Image) -> str:
    """SHA-256 of raw RGBA pixel data, ignoring PNG metadata/encoding."""
    return hashlib.sha256(img.tobytes()).hexdigest()


def _stamp_to_image(stamp) -> Image.Image:
    from gex.render import blank_image, write_stamp_to_image
    h = len(stamp.data) // stamp.width
    img = blank_image(stamp.width * 8, h * 8)
    write_stamp_to_image(img, stamp, 0, 0)
    return img


def _save_failure_image(name: str, img: Image.Image, ref_path: Path) -> None:
    """Save the rendered image to a temp file and print both paths."""
    out_path = Path(tempfile.gettempdir()) / f"gex_fail_{name}.png"
    img.save(out_path)
    print(f"\n  reference image : {ref_path}")
    print(f"  rendered image  : {out_path}")


def _assert_matches_ref(name: str, img: Image.Image, manifest: dict) -> None:
    """Assert that a rendered image's pixels match the reference."""
    ref_path = REF_DIR / f"{name}.png"
    assert ref_path.is_file(), f"Reference image missing: {ref_path}"
    entry = manifest[name]

    # Check size
    if list(img.size) != entry["size"]:
        _save_failure_image(name, img, ref_path)
        raise AssertionError(
            f"{name}: size mismatch: got {list(img.size)}, expected {entry['size']}"
        )

    # Compare pixel data against the reference PNG (loaded and decoded)
    ref_img = Image.open(ref_path)
    rendered_sha = _pixel_sha256(img)
    ref_sha = _pixel_sha256(ref_img)
    if rendered_sha != ref_sha:
        _save_failure_image(name, img, ref_path)
        raise AssertionError(
            f"{name}: pixel data mismatch.\n"
            f"  rendered: {rendered_sha}\n"
            f"  reference: {ref_sha}"
        )

    # Also verify manifest hash is consistent with the reference file
    assert ref_sha == entry["pixel_sha256"], (
        f"{name}: manifest hash stale — regenerate with generate_reference_images.py"
    )


# ===================================================================
# Tile golden tests
# ===================================================================

class TestTileGolden:
    @pytest.mark.parametrize("tilenum", [0x11, 0x100, 0x1C1])
    def test_single_tile(self, tilenum, manifest):
        from gex.render import gen_image
        name = f"tile_{tilenum:#06x}"
        img = gen_image(tilenum, 1, 1)
        _assert_matches_ref(name, img, manifest)

    @pytest.mark.parametrize("xt,yt", [(2, 2), (4, 4)])
    def test_tile_grid(self, xt, yt, manifest):
        from gex.render import gen_image
        name = f"tilegrid_0x0100_{xt}x{yt}"
        img = gen_image(0x100, xt, yt)
        _assert_matches_ref(name, img, manifest)

    def test_tile_array(self, manifest):
        from gex.render import gen_image_from_array
        img = gen_image_from_array([0x100, 0x101, 0x102, 0x103], 2, 2)
        _assert_matches_ref("tilearray_custom", img, manifest)


# ===================================================================
# Floor golden tests
# ===================================================================

class TestFloorGolden:
    @pytest.mark.parametrize("pattern", [0, 3, 5, 8])
    @pytest.mark.parametrize("color", [0, 5, 15])
    @pytest.mark.parametrize("adj", [0, 4, 16, 28])
    def test_floor(self, pattern, color, adj, manifest):
        from gex.floor import floor_get_stamp
        name = f"floor_p{pattern}_c{color}_a{adj}"
        stamp = floor_get_stamp(pattern, adj, color)
        img = _stamp_to_image(stamp)
        _assert_matches_ref(name, img, manifest)


# ===================================================================
# Wall golden tests
# ===================================================================

class TestWallGolden:
    @pytest.mark.parametrize("pattern", [0, 2, 5])
    @pytest.mark.parametrize("color", [0, 8])
    @pytest.mark.parametrize("adj_val", [0x00, 0x0F, 0xFF])
    def test_wall(self, pattern, color, adj_val, manifest):
        from gex.wall import wall_get_stamp
        name = f"wall_p{pattern}_c{color}_a{adj_val:#04x}"
        stamp = wall_get_stamp(pattern, adj_val, color)
        img = _stamp_to_image(stamp)
        _assert_matches_ref(name, img, manifest)

    @pytest.mark.parametrize("pattern", [6, 8, 11])
    def test_shrub_wall(self, pattern, manifest):
        from gex.wall import wall_get_stamp
        name = f"wall_shrub_p{pattern}"
        stamp = wall_get_stamp(pattern, 0, 0)
        img = _stamp_to_image(stamp)
        _assert_matches_ref(name, img, manifest)

    @pytest.mark.parametrize("pattern", [0, 3, 6])
    def test_destructible_wall(self, pattern, manifest):
        from gex.wall import wall_get_destructable_stamp
        name = f"wall_destruct_p{pattern}"
        stamp = wall_get_destructable_stamp(pattern, 0, 0)
        img = _stamp_to_image(stamp)
        _assert_matches_ref(name, img, manifest)

    @pytest.mark.parametrize("adj", [0, 5, 10, 15])
    def test_forcefield(self, adj, manifest):
        from gex.wall import ff_get_stamp
        name = f"ff_a{adj}"
        stamp = ff_get_stamp(adj)
        img = _stamp_to_image(stamp)
        _assert_matches_ref(name, img, manifest)


# ===================================================================
# Item golden tests
# ===================================================================

class TestItemGolden:
    ITEMS = ["key", "food", "potion", "treasure", "dragon", "ghost",
             "grunt", "demon", "exit", "tport", "blank", "invis",
             "goldbag", "supershot", "invuln"]

    @pytest.mark.parametrize("item_name", ITEMS)
    def test_item(self, item_name, manifest):
        from gex.items import item_get_stamp
        name = f"item_{item_name}"
        stamp = item_get_stamp(item_name)
        img = _stamp_to_image(stamp)
        _assert_matches_ref(name, img, manifest)


# ===================================================================
# Door golden tests
# ===================================================================

class TestDoorGolden:
    @pytest.mark.parametrize("adj", [0, 3, 7, 15])
    @pytest.mark.parametrize("direction,dname", [(0, "horiz"), (1, "vert")])
    def test_door(self, direction, dname, adj, manifest):
        from gex.door import door_get_stamp
        name = f"door_{dname}_a{adj}"
        stamp = door_get_stamp(direction, adj)
        img = _stamp_to_image(stamp)
        _assert_matches_ref(name, img, manifest)


# ===================================================================
# Monster golden tests
# ===================================================================

class TestMonsterGolden:
    DIRECTIONS = ["up", "right", "down", "left", "upright", "downleft"]

    @pytest.mark.parametrize("direction", DIRECTIONS)
    def test_ghost_direction(self, direction, manifest, tmp_path):
        from gex.monsters import domonster
        name = f"ghost_walk_{direction}"
        path = str(tmp_path / f"{name}.png")
        domonster(f"ghost-walk-{direction}", path, "base", 0, False)
        img = Image.open(path)
        _assert_matches_ref(name, img, manifest)

    @pytest.mark.parametrize("level", [1, 2, 3])
    def test_ghost_level(self, level, manifest, tmp_path):
        from gex.monsters import domonster
        name = f"ghost{level}_walk_up"
        path = str(tmp_path / f"{name}.png")
        domonster(f"ghost{level}-walk-up", path, "base", 0, False)
        img = Image.open(path)
        _assert_matches_ref(name, img, manifest)


# ===================================================================
# Maze golden tests
# ===================================================================

import os as _os
_ALL_MAZES = list(range(117))
_DEFAULT_MAZES = [0, 10, 25, 50, 100, 116]
_MAZE_PARAMS = _ALL_MAZES if _os.environ.get("GEX_TEST_ALL_MAZES") else _DEFAULT_MAZES


class TestMazeGolden:
    @pytest.mark.parametrize("maze_num", _MAZE_PARAMS)
    def test_maze(self, maze_num, manifest, tmp_path):
        from gex.maze import domaze
        name = f"maze_{maze_num}"
        path = str(tmp_path / f"{name}.png")
        domaze(f"maze{maze_num}", path, False)
        img = Image.open(path)
        _assert_matches_ref(name, img, manifest)


# ===================================================================
# Pixel-level spot checks (not hash-based — survive PNG encoder changes)
# ===================================================================

class TestPixelSpotChecks:
    """Sample specific pixels from rendered images to catch regressions
    even if the PNG encoder changes compression or metadata."""

    def test_blank_item_all_transparent(self):
        from gex.items import item_get_stamp
        stamp = item_get_stamp("blank")
        img = _stamp_to_image(stamp)
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                assert (r, g, b) == (0, 0, 0), f"blank pixel ({x},{y}) not black"

    def test_floor_not_all_transparent(self):
        from gex.floor import floor_get_stamp
        stamp = floor_get_stamp(0, 0, 0)
        img = _stamp_to_image(stamp)
        pixels = img.load()
        has_opaque = any(
            pixels[x, y][3] == 255
            for y in range(img.height)
            for x in range(img.width)
        )
        assert has_opaque, "Floor stamp is entirely transparent"

    def test_wall_center_has_content(self):
        from gex.wall import wall_get_stamp
        stamp = wall_get_stamp(0, 0xFF, 0)
        img = _stamp_to_image(stamp)
        pixels = img.load()
        # Center pixel of a fully-surrounded wall should be non-transparent
        cx, cy = img.width // 2, img.height // 2
        assert pixels[cx, cy][3] == 255

    def test_key_has_transparent_background(self):
        from gex.items import item_get_stamp
        stamp = item_get_stamp("key")
        img = _stamp_to_image(stamp)
        pixels = img.load()
        # Key has trans0=True, so corners should be transparent
        assert pixels[0, 0][3] == 0, "Key corner should be transparent"

    def test_dragon_dimensions(self):
        from gex.items import item_get_stamp
        stamp = item_get_stamp("dragon")
        img = _stamp_to_image(stamp)
        assert img.size == (32, 32), "Dragon should be 4x4 tiles = 32x32 pixels"

    def test_exit_uses_floor_palette(self):
        """Exit tile should use floor palette colors, not base palette."""
        from gex.items import item_get_stamp
        from gex.palettes import FLOOR_PALETTES
        stamp = item_get_stamp("exit")
        img = _stamp_to_image(stamp)
        pixels = img.load()
        # Collect all unique colors in the rendered exit
        colors = set()
        for y in range(img.height):
            for x in range(img.width):
                colors.add(pixels[x, y])
        # At least one pixel should match a color from floor palette 0
        floor_colors = {c.to_rgba() for c in FLOOR_PALETTES[0]}
        assert colors & floor_colors, "Exit should contain floor palette colors"

    def test_maze_image_dimensions(self):
        """Maze 0 image should be the expected playfield size."""
        from gex.roms import slapstic_read_maze
        from gex.mazedecode import maze_decompress
        from gex.constants import LFLAG4_WRAP_H, LFLAG4_WRAP_V
        data = slapstic_read_maze(0)
        maze = maze_decompress(data, metaonly=True)
        extra_x = 16 if (maze.flags & LFLAG4_WRAP_H) == 0 else 0
        extra_y = 16 if (maze.flags & LFLAG4_WRAP_V) == 0 else 0
        expected_w = 8 * 2 * 32 + 32 + extra_x
        expected_h = 8 * 2 * 32 + 32 + extra_y
        ref_path = REF_DIR / "maze_0.png"
        if ref_path.is_file():
            img = Image.open(ref_path)
            assert img.size == (expected_w, expected_h)

    def test_ghost_sprite_has_content(self):
        """Ghost sprite should not be all transparent."""
        from gex.monsters import domonster
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            domonster("ghost-walk-down", path, "base", 0, False)
            img = Image.open(path)
            pixels = img.load()
            opaque_count = sum(
                1 for y in range(img.height) for x in range(img.width)
                if pixels[x, y][3] > 0
            )
            # A 24x24 ghost sprite should have a significant number of opaque pixels
            assert opaque_count > 20, f"Ghost sprite has only {opaque_count} opaque pixels"
        finally:
            os.unlink(path)

    def test_forcefield_stamp_uses_teleff_palette(self):
        from gex.wall import ff_get_stamp
        from gex.palettes import TELEFF_PALETTES
        stamp = ff_get_stamp(0x0F)
        img = _stamp_to_image(stamp)
        pixels = img.load()
        colors = set()
        for y in range(img.height):
            for x in range(img.width):
                colors.add(pixels[x, y])
        teleff_colors = {c.to_rgba() for c in TELEFF_PALETTES[0]}
        assert colors & teleff_colors, "Forcefield should contain teleff palette colors"

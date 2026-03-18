"""Core rendering: tile parsing, image generation, stamp system."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from PIL import Image

from .palettes import IRGB, GAUNTLET_PALETTES, Palette
from .roms import get_romset, get_tile_data_from_file


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

TileLinePlane = bytes          # 8 bytes from one ROM plane
TileLineMerged = list[int]     # 8 pixel values (4-bit) after merging planes
TileData = list[TileLineMerged]  # 8 lines of merged pixel data


@dataclass
class Stamp:
    width: int
    numbers: list[int]
    ptype: str
    pnum: int
    trans0: bool = False
    nudgex: int = 0
    nudgey: int = 0
    data: list[TileData] = field(default_factory=list)


def byte_to_bits(databyte: int) -> list[int]:
    """Convert a byte to 8 bit values (MSB first), where 0 means bit was set."""
    return [0 if (databyte >> i) & 1 else 1 for i in range(7, -1, -1)]


def merge_planes(planes: list[list[int]]) -> TileLineMerged:
    return [
        p3 * 8 + p2 * 4 + p1 * 2 + p0
        for p0, p1, p2, p3 in zip(planes[0], planes[1], planes[2], planes[3])
    ]


@lru_cache(maxsize=None)
def get_parsed_tile(tilenum: int) -> TileData:
    realtilenum, rom_files = get_romset(tilenum)
    planedata = [get_tile_data_from_file(rf, realtilenum) for rf in rom_files]
    return [
        merge_planes([byte_to_bits(plane[line]) for plane in planedata])
        for line in range(8)
    ]


# ---------------------------------------------------------------------------
# Image utilities
# ---------------------------------------------------------------------------

def blank_image(x: int, y: int) -> Image.Image:
    return Image.new("RGBA", (x, y), (0, 0, 0, 0))


def write_tile_to_image(
    img: Image.Image,
    tile: TileData,
    palette: Palette,
    trans0: bool,
    x: int,
    y: int,
) -> None:
    pixels = img.load()
    w, h = img.size
    for j in range(8):
        for i in range(8):
            px, py = x + i, y + j
            if px < 0 or py < 0 or px >= w or py >= h:
                continue
            tc = tile[j][i]
            if tc == 0 and trans0:
                continue
            pixels[px, py] = palette[tc].to_rgba()


def fill_stamp(stamp: Stamp) -> None:
    stamp.data = [get_parsed_tile(num) for num in stamp.numbers]


def gen_stamp_from_array(
    tiles: list[int], width: int, ptype: str, pnum: int
) -> Stamp:
    stamp = Stamp(width=width, numbers=tiles, ptype=ptype, pnum=pnum)
    fill_stamp(stamp)
    return stamp


def write_stamp_to_image(
    img: Image.Image, stamp: Stamp, xloc: int, yloc: int
) -> None:
    p = GAUNTLET_PALETTES[stamp.ptype][stamp.pnum]
    for idx, tile in enumerate(stamp.data):
        y, x = divmod(idx, stamp.width)
        write_tile_to_image(img, tile, p, stamp.trans0, xloc + x * 8, yloc + y * 8)


def gen_image(tilenum: int, xtiles: int, ytiles: int, pal_type: str = "base", pal_num: int = 0) -> Image.Image:
    t = list(range(tilenum, tilenum + xtiles * ytiles))
    return gen_image_from_array(t, xtiles, ytiles, pal_type, pal_num)


def gen_image_from_array(
    tiles: list[int], xtiles: int, ytiles: int, pal_type: str = "base", pal_num: int = 0
) -> Image.Image:
    stamp = gen_stamp_from_array(tiles, xtiles, pal_type, pal_num)
    img = blank_image(8 * xtiles, 8 * ytiles)
    write_stamp_to_image(img, stamp, 0, 0)
    return img


def save_to_png(filename: str, img: Image.Image) -> None:
    img.save(filename, "PNG")


def render_stamp_to_file(stamp: Stamp, output: str) -> None:
    """Render a single stamp to a PNG file."""
    height = len(stamp.numbers) // stamp.width
    img = blank_image(8 * stamp.width, 8 * height)
    write_stamp_to_image(img, stamp, 0, 0)
    save_to_png(output, img)

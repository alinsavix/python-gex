"""Core rendering: tile parsing, image generation, stamp system."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PIL import Image

from .palettes import IRGB, GAUNTLET_PALETTES, Palette
from .roms import get_romset, _rom_dir


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


# ---------------------------------------------------------------------------
# Tile data reading
# ---------------------------------------------------------------------------

def get_tile_data_from_file(filepath: str, tilenum: int) -> bytes:
    rom_dir = _rom_dir()
    with open(rom_dir / filepath, "rb") as f:
        f.seek(tilenum * 8)
        data = f.read(8)
    if len(data) != 8:
        raise RuntimeError("Failed to read full tile from file")
    return data


def byte_to_bits(databyte: int) -> list[int]:
    """Convert a byte to 8 bit values (MSB first), where 0 means bit was set."""
    res: list[int] = []
    for i in range(7, -1, -1):
        if (databyte >> i) & 1:
            res.append(0)
        else:
            res.append(1)
    return res


def merge_planes(planes: list[list[int]]) -> TileLineMerged:
    merged: TileLineMerged = []
    for i in range(8):
        val = (planes[3][i] * 8) + (planes[2][i] * 4) + (planes[1][i] * 2) + planes[0][i]
        merged.append(val)
    return merged


def get_parsed_tile(tilenum: int) -> TileData:
    realtilenum, rom_files = get_romset(tilenum)
    planedata = [get_tile_data_from_file(rom_files[p], realtilenum) for p in range(4)]

    fulltile: TileData = []
    for line in range(8):
        linedata = [byte_to_bits(planedata[p][line]) for p in range(4)]
        fulltile.append(merge_planes(linedata))
    return fulltile


# ---------------------------------------------------------------------------
# Image utilities
# ---------------------------------------------------------------------------

def blank_image(x: int, y: int) -> Image.Image:
    return Image.new("RGBA", (x, y), (0, 0, 0, 0))


def irgb_to_rgba(color: IRGB) -> tuple[int, int, int, int]:
    return color.to_rgba()


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
    height = len(stamp.numbers) // stamp.width
    stamp.data = [None] * len(stamp.numbers)  # type: ignore[list-item]
    tc = 0
    for y in range(height):
        for x in range(stamp.width):
            stamp.data[(stamp.width * y) + x] = get_parsed_tile(stamp.numbers[tc])
            tc += 1


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
    height = len(stamp.data) // stamp.width
    for y in range(height):
        for x in range(stamp.width):
            write_tile_to_image(
                img,
                stamp.data[(stamp.width * y) + x],
                p,
                stamp.trans0,
                xloc + (x * 8),
                yloc + (y * 8),
            )


def gen_image(tilenum: int, xtiles: int, ytiles: int, pal_type: str = "base", pal_num: int = 0) -> Image.Image:
    t = [tilenum + i for i in range(xtiles * ytiles)]
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

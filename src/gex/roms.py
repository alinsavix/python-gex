"""ROM reading utilities: split read, code ROMs, tile ROMs, slapstic."""

from __future__ import annotations

import os
import struct
from pathlib import Path
from typing import NamedTuple

from .constants import MAX_MAZE_NUM

SLAPSTIC_START = 0x038000
CODE_ROM_START = 0x040000


class GexError(Exception):
    """Application-level error for gex."""


def _rom_dir() -> Path:
    """Return the directory containing ROM files.

    Checks the ``GEX_ROM_DIR`` environment variable first, falling back
    to a ``ROMs`` directory in the current working directory.
    """
    return Path(os.environ.get("GEX_ROM_DIR", "ROMs"))


# ---------------------------------------------------------------------------
# ROM split read -- interleaved byte reading from paired ROM files
# ---------------------------------------------------------------------------

def rom_split_read(roms: list[str], offset: int, count: int, exact: bool = True) -> bytes:
    """Read interleaved bytes from a pair of ROM files.

    When *exact* is True (the default) a GexError is raised if fewer than
    *count* bytes are available.  Pass exact=False for callers that treat
    *count* as an upper bound (e.g. reading a variable-length record with a
    known maximum size).
    """
    if offset >= SLAPSTIC_START:
        offset -= SLAPSTIC_START

    expected = count
    rom_dir = _rom_dir()
    with open(rom_dir / roms[0], "rb") as f0, open(rom_dir / roms[1], "rb") as f1:
        f0.seek(offset // 2)
        f1.seek(offset // 2)

        if offset % 2:
            f0.read(1)  # skip misaligned byte

        handles = (f0, f1)
        buf = bytearray()
        for i in range(count):
            b = handles[(i + offset) % 2].read(1)
            if not b:
                break
            buf.append(b[0])

    if exact and len(buf) != expected:
        raise GexError(
            f"rom_split_read: short read ({len(buf)} of {expected} bytes)"
            f" at offset {offset} in {roms}"
        )
    return bytes(buf)


# ---------------------------------------------------------------------------
# Tile ROMs
# ---------------------------------------------------------------------------

class Romset(NamedTuple):
    offset: int
    roms: list[str]


TILE_ROMS = [
    [
        "136043-1111.1a",
        "136043-1113.1l",
        "136043-1115.2a",
        "136043-1117.2l",
    ],
    [
        "136037-112.1b",
        "136037-114.1mn",
        "136037-116.2b",
        "136037-118.2mn",
    ],
    [
        "136043-1123.1c",
        "136043-1124.1p",
        "136043-1125.2c",
        "136043-1126.2p",
    ],
]

TILE_ROM_SETS = [
    Romset(0x800, TILE_ROMS[0]),
    Romset(0x0, TILE_ROMS[0]),
    Romset(0x800, TILE_ROMS[1]),
    Romset(0x0, TILE_ROMS[1]),
    Romset(0x0, TILE_ROMS[2]),
]


def get_romset(tilenum: int) -> tuple[int, list[str]]:
    """Returns (actual_tile_number, rom_file_list) for a given tile number."""
    whichbank = tilenum // 0x800
    rs = TILE_ROM_SETS[whichbank]
    actualtile = (tilenum % 0x800) + rs.offset
    return actualtile, rs.roms


# ---------------------------------------------------------------------------
# Code ROMs
# ---------------------------------------------------------------------------

CODE_ROMS = [
    ["136043-1109.7a", "136043-1110.7b"],
    ["136043-1121.6a", "136043-1122.6b"],
]

CODE_ROM_SETS = [
    Romset(0x8000, CODE_ROMS[0]),
    Romset(0x0000, CODE_ROMS[0]),
    Romset(0x8000, CODE_ROMS[1]),
    Romset(0x0000, CODE_ROMS[1]),
]


def coderom_get_by_addr(addr: int) -> tuple[list[str], int]:
    a = addr - CODE_ROM_START
    bank = a // 0x8000
    rs = CODE_ROM_SETS[bank]
    offset = a % 0x8000 + rs.offset
    return rs.roms, offset


def coderom_get_bytes(addr: int, count: int) -> bytes:
    rompair, offset = coderom_get_by_addr(addr)
    return rom_split_read(rompair, offset, count)


# ---------------------------------------------------------------------------
# Slapstic ROMs
# ---------------------------------------------------------------------------

SLAPSTIC_ROMS = ["136043-1105.10a", "136043-1106.10b"]

SLAPSTIC_BANK_INFO = [
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x54, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x95,
    0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xFE, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x03, 0xFC, 0x0E,
]


def get_tile_data_from_file(filepath: str, tilenum: int) -> bytes:
    """Read 8 bytes of tile data from a ROM file at the given tile index."""
    with open(_rom_dir() / filepath, "rb") as f:
        f.seek(tilenum * 8)
        data = f.read(8)
    if len(data) != 8:
        raise RuntimeError("Failed to read full tile from file")
    return data


def slapstic_read_bytes(offset: int, count: int, exact: bool = True) -> bytes:
    if offset >= SLAPSTIC_START:
        offset -= SLAPSTIC_START
    return rom_split_read(SLAPSTIC_ROMS, offset, count, exact=exact)


def slapstic_maze_get_bank(mazenum: int) -> int:
    if mazenum < 0 or mazenum > MAX_MAZE_NUM:
        raise GexError(f"Invalid maze number requested (must be 0 <= x <= {MAX_MAZE_NUM})")
    bank_byte = SLAPSTIC_BANK_INFO[mazenum // 4]
    shift = (mazenum % 4) * 2
    return (bank_byte >> shift) & 0x3


def slapstic_read_maze_offset(mazenum: int) -> int:
    buf = slapstic_read_bytes(0x03800C + (4 * mazenum), 4)
    return struct.unpack(">I", buf)[0]


def slapstic_maze_get_real_addr(mazenum: int) -> int:
    bank = slapstic_maze_get_bank(mazenum)
    return slapstic_read_maze_offset(mazenum) + (0x2000 * bank)


def slapstic_read_maze(mazenum: int) -> list[int]:
    addr = slapstic_maze_get_real_addr(mazenum)
    b = slapstic_read_bytes(addr, 512, exact=False)
    for i, byte in enumerate(b):
        if i >= 11 and byte == 0:
            return list(b[:i + 1])
    return list(b)

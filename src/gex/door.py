"""Door stamps and rendering."""

from __future__ import annotations

from .render import Stamp, gen_stamp_from_array
from .roms import GexError

DOOR_HORIZ = 0
DOOR_VERT = 1

# First tile numbers; next three are sequential for all door types
DOOR_STAMPS = [
    0x0000,  # nothing adjacent
    0x0000,  # only adjacent up
    0x0000,  # only adjacent right
    0x1D34,  # up right
    0x0000,  # only adjacent down
    0x0000,  # only adjacent down and up
    0x1D2C,  # down right
    0x1D1C,  # up-right-down
    0x0000,  # only adjacent left
    0x1D38,  # left-up
    0x0000,  # only adjacent left and right
    0x1D24,  # up-left-right
    0x1D30,  # left-down
    0x1D18,  # up-down-left
    0x1D20,  # right left down
    0x1D28,  # up down left right
]


def door_get_tiles(door_dir: int, door_adj: int) -> list[int]:
    m = DOOR_STAMPS[door_adj]
    if m == 0:
        raise GexError(f"No door stamp for adjacency {door_adj}")
    return list(range(m, m + 4))


def door_get_stamp(door_dir: int, door_adj: int) -> Stamp:
    try:
        tiles = door_get_tiles(door_dir, door_adj)
    except GexError:
        from .items import item_get_stamp
        return item_get_stamp("hdoor" if door_dir == DOOR_HORIZ else "vdoor")
    stamp = gen_stamp_from_array(tiles, 2, "base", 0)
    stamp.trans0 = True
    return stamp

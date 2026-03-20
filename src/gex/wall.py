"""Wall tile stamps, shrub stamps, forcefield stamps, and rendering."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .rand import SeededRandom
from .render import Stamp, gen_stamp_from_array, render_stamp_to_file

_DATA_DIR = Path(__file__).parent / "data"


def _load_jsonc(path: Path):
    """Load a JSON-with-comments (.jsonc) file, stripping // and /* */ comments."""
    text = path.read_text()
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return json.loads(text)


def _load_wall_stamps() -> list[list[int]]:
    return _load_jsonc(_DATA_DIR / "wall_stamps.jsonc")


def _load_wall_data() -> dict:
    return _load_jsonc(_DATA_DIR / "wall_data.jsonc")


# Tile ROM indices for wall sprites.  There are 6 wall patterns (patterns 0–5),
# each with 68 adjacency variants.  Each variant is 4 tiles arranged in a 2×2
# stamp.  Tile numbers are absolute indices into the Gauntlet II tile ROMs.
#
# Pattern boundaries:
#   Pattern 0:  WALL_STAMPS[  0 ..  67]   (stone/brick - original Gauntlet II set)
#   Pattern 1:  WALL_STAMPS[ 68 .. 135]   (dungeon style)
#   Pattern 2:  WALL_STAMPS[136 .. 203]   (castle style)
#   Pattern 3:  WALL_STAMPS[204 .. 271]   (cave style)
#   Pattern 4:  WALL_STAMPS[272 .. 339]   (ice/crystal style)
#   Pattern 5:  WALL_STAMPS[340 .. 407]   (used for destructible wall fallback)
WALL_STAMPS: list[list[int]] = _load_wall_stamps()

_wall_data = _load_wall_data()
SHRUB_STAMPS:             list[list[int]] = _wall_data["shrub_stamps"]
SHRUB_DESTRUCT_STAMPS:    list[list[int]] = _wall_data["shrub_destruct_stamps"]
SHRUB_OTHER_STAMPS:       list[list[int]] = _wall_data["shrub_other_stamps"]
SHRUB_OTHER_ORDER_STAMPS: list[list[int]] = _wall_data["shrub_other_order_stamps"]
FF_MAP:                   list[list[int]] = _wall_data["ff_map"]
WALL_MAP:                 list[int]       = _wall_data["wall_map"]
SHRUB_WALL_MAP:           list[int]       = _wall_data["shrub_wall_map"]


def wall_get_tiles(wall_num: int, wall_adj: int, rand: SeededRandom) -> list[int]:
    wm = WALL_MAP
    st = WALL_STAMPS

    # shrub level, but not 6 or 11
    if wall_num >= 6 and wall_num not in (6, 11):
        adder = 0
        if wall_num in (7, 12):
            adder = 6
        r = rand.intn(6)
        return list(SHRUB_OTHER_ORDER_STAMPS[r + adder])

    # shrub level, exactly 6 or 11
    if wall_num >= 6:
        wm = SHRUB_WALL_MAP
        st = SHRUB_STAMPS
        wall_num = 0

    m = wm[wall_adj]
    return list(st[(68 * wall_num) + m])


def wall_get_stamp(wall_num: int, wall_adj: int, wall_color: int, rand: SeededRandom | None = None) -> Stamp:
    if rand is None:
        rand = SeededRandom(5)
    tiles = wall_get_tiles(wall_num, wall_adj, rand)
    wp, wc = ("shrub", 0) if wall_num >= 6 else ("wall", wall_color)
    return gen_stamp_from_array(tiles, 2, wp, wc)


def wall_get_destructable_stamp(wall_num: int, wall_adj: int, wall_color: int, rand: SeededRandom | None = None) -> Stamp:
    if wall_num < 6:
        return wall_get_stamp(5, wall_adj, wall_color, rand)
    tiles = SHRUB_DESTRUCT_STAMPS[0]
    return gen_stamp_from_array(tiles, 2, "shrub", 0)


def ff_get_stamp(ff_adj: int) -> Stamp:
    tiles = FF_MAP[ff_adj]
    return gen_stamp_from_array(tiles, 2, "teleff", 0)


_WALL_ADJ_MAP = {"ul": 0x01, "u": 0x02, "ur": 0x04, "l": 0x08,
                 "r": 0x10, "dl": 0x20, "d": 0x40, "dr": 0x80}


def dowall(arg: str, output: str) -> None:
    split = arg.split("-")
    wall_num = -1
    wall_color = 0
    wall_adj = 0

    for ss in split:
        if ss.startswith("wall") and ss[4:].isdigit():
            wall_num = int(ss[4:])
        elif ss.startswith("c") and ss[1:].isdigit():
            wall_color = int(ss[1:])
        elif ss in _WALL_ADJ_MAP:
            wall_adj += _WALL_ADJ_MAP[ss]

    print(f"Wall number: {wall_num}   color: {wall_color}   adj: {wall_adj}")
    render_stamp_to_file(wall_get_stamp(wall_num, wall_adj, wall_color), output)

"""Door stamps and rendering."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .render import Stamp, gen_stamp_from_array
from .roms import GexError

_DATA_DIR = Path(__file__).parent / "data"

DOOR_HORIZ = 0
DOOR_VERT = 1


def _load_jsonc(path: Path):
    """Load a JSON-with-comments (.jsonc) file, stripping // and /* */ comments."""
    text = path.read_text()
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return json.loads(text)


DOOR_STAMPS: list[int] = _load_jsonc(_DATA_DIR / "door_stamps.jsonc")["door_stamps"]


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

"""Item stamps and rendering."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from .render import Stamp, fill_stamp, render_stamp_to_file
from .roms import GexError

_DATA_DIR = Path(__file__).parent / "data"


def _tr(start: int, count: int) -> list[int]:
    """Generate a range of sequential tile numbers."""
    return list(range(start, start + count))


def _load_jsonc(path: Path):
    """Load a JSON-with-comments (.jsonc) file, stripping // and /* */ comments."""
    text = path.read_text()
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return json.loads(text)


def _load_item_stamps() -> dict[str, dict]:
    return _load_jsonc(_DATA_DIR / "item_stamps.jsonc")


# Item sprite definitions.  Each entry maps an item name to its rendering
# parameters.  'numbers' contains absolute tile ROM indices (or a pre-expanded
# sequential range).  'ptype'/'pnum' select the colour palette.
# Tile indices reference the Gauntlet II tile ROMs as loaded by render.py.
ITEM_STAMPS: dict[str, dict] = _load_item_stamps()


@lru_cache(maxsize=None)
def item_get_stamp(item_type: str) -> Stamp:
    info = ITEM_STAMPS.get(item_type)
    if info is None:
        raise GexError(f"requested bad item: {item_type}")
    stamp = Stamp(
        width=info["width"],
        numbers=info["numbers"],
        ptype=info["ptype"],
        pnum=info["pnum"],
        trans0=info.get("trans0", False),
        nudgex=info.get("nudgex", 0),
        nudgey=info.get("nudgey", 0),
    )
    fill_stamp(stamp)
    return stamp


def doitem(arg: str, output: str) -> None:
    split = arg.split("-")
    item_type = next((ss for ss in split if ss in ITEM_STAMPS), "")
    render_stamp_to_file(item_get_stamp(item_type), output)

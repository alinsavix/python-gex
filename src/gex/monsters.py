"""Monster/ghost data and rendering."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .render import Stamp, gen_image, save_to_png

_DATA_DIR = Path(__file__).parent / "data"

# Animation types
MobAnimFrames = list[int]
MobAnimsDir = dict[str, MobAnimFrames]
MobAnims = dict[str, MobAnimsDir]


@dataclass
class Monster:
    xsize: int
    ysize: int
    ptype: str
    pnum: int
    anims: MobAnims = field(default_factory=dict)


def _load_jsonc(path: Path):
    """Load a JSON-with-comments (.jsonc) file, stripping // and /* */ comments."""
    text = path.read_text()
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return json.loads(text)


def _load_monsters() -> dict[str, Monster]:
    raw = _load_jsonc(_DATA_DIR / "monsters.jsonc")
    return {name: Monster(**entry) for name, entry in raw.items()}


MONSTERS: dict[str, Monster] = _load_monsters()

# Convenience alias kept for backwards compatibility.
GHOST_ANIMS: MobAnims = MONSTERS["ghost"].anims

_MONSTER_ACTIONS = {"walk", "fight", "attack"}
_MONSTER_DIRS = {"upright", "upleft", "downright", "downleft", "up", "right", "down", "left"}


def domonster(arg: str, output: str, pal_type: str, pal_num: int, animate: bool) -> tuple[str, int]:
    """Returns (pal_type, pal_num) after modification."""
    split = arg.split("-")
    monster_type = ""
    monster_action = "walk"
    monster_dir = "up"
    monster_level = 1

    for ss in split:
        matched_type = next(
            (t for t in MONSTERS if ss == t or (ss.startswith(t) and ss[len(t):].isdigit())),
            None,
        )
        if matched_type:
            monster_type = matched_type
            level_str = ss[len(matched_type):]
            if level_str:
                monster_level = int(level_str)
        elif ss in _MONSTER_ACTIONS:
            monster_action = ss
        elif ss in _MONSTER_DIRS:
            monster_dir = ss

    mon = MONSTERS[monster_type]
    pal_type = mon.ptype
    pal_num = mon.pnum + (monster_level + 1)

    if not animate:
        t = mon.anims[monster_action][monster_dir][0]
        img = gen_image(t, mon.xsize, mon.ysize, pal_type, pal_num)
        save_to_png(output, img)

    return pal_type, pal_num

"""Monster/ghost data and rendering."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .render import Stamp, gen_image, save_to_png


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


GHOST_ANIMS: MobAnims = {
    "walk": {
        "up":        [0x890, 0x899, 0x8A2, 0x8AB],
        "upright":   [0x86C, 0x875, 0x87E, 0x887],
        "right":     [0x848, 0x851, 0x85A, 0x863],
        "downright": [0x824, 0x82D, 0x836, 0x83F],
        "down":      [0x800, 0x809, 0x812, 0x81B],
        "downleft":  [0x900, 0x909, 0x912, 0x91B],
        "left":      [0x8D8, 0x8E1, 0x8EA, 0x8F3],
        "upleft":    [0x8B4, 0x8BD, 0x8C6, 0x8CF],
    },
}

MONSTERS: dict[str, Monster] = {
    "ghost": Monster(xsize=3, ysize=3, ptype="base", pnum=0, anims=GHOST_ANIMS),
}

RE_MONSTER_TYPE = re.compile(r"^(ghost)(\d+)?")
RE_MONSTER_ACTION = re.compile(r"^(walk|fight|attack)")
RE_MONSTER_DIR = re.compile(r"^(up|upright|right|downright|down|downleft|left|upleft)")


def domonster(arg: str, output: str, pal_type: str, pal_num: int, animate: bool) -> tuple[str, int]:
    """Returns (pal_type, pal_num) after modification."""
    split = arg.split("-")
    monster_type = ""
    monster_action = "walk"
    monster_dir = "up"
    monster_level = 1

    for ss in split:
        m = RE_MONSTER_TYPE.match(ss)
        if m:
            monster_type = m.group(1)
            if m.group(2):
                monster_level = int(m.group(2))
            continue
        m = RE_MONSTER_ACTION.match(ss)
        if m:
            monster_action = m.group(1)
            continue
        m = RE_MONSTER_DIR.match(ss)
        if m:
            monster_dir = m.group(1)

    mon = MONSTERS[monster_type]
    pal_type = mon.ptype
    pal_num = mon.pnum + (monster_level + 1)

    if not animate:
        t = mon.anims[monster_action][monster_dir][0]
        img = gen_image(t, mon.xsize, mon.ysize, pal_type, pal_num)
        save_to_png(output, img)

    return pal_type, pal_num

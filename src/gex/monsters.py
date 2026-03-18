"""Monster/ghost data and rendering."""

from __future__ import annotations

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

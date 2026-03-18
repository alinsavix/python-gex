"""Item stamps and rendering."""

from __future__ import annotations

import re
from functools import lru_cache

from .render import Stamp, blank_image, fill_stamp, write_stamp_to_image, save_to_png
from .roms import GexError


def _tr(start: int, count: int) -> list[int]:
    """Generate a range of sequential tile numbers."""
    return list(range(start, start + count))


ITEM_STAMPS: dict[str, dict] = {
    "blank":            dict(width=2, numbers=[0, 0, 0, 0], ptype="base", pnum=0, trans0=False),
    "key":              dict(width=2, numbers=_tr(0xAFC, 4), ptype="base", pnum=1, trans0=True),
    "keyring":          dict(width=3, numbers=_tr(0x1D76, 6), ptype="base", pnum=1, trans0=True),
    "food":             dict(width=3, numbers=_tr(0x963, 9), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "ifood1":           dict(width=3, numbers=_tr(0x96C, 9), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "ifood2":           dict(width=3, numbers=_tr(0x975, 9), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "ifood3":           dict(width=3, numbers=_tr(0x97E, 9), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "mfood":            dict(width=3, numbers=_tr(0x277B, 9), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "pfood":            dict(width=3, numbers=_tr(0x25ED, 9), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "potion":           dict(width=2, numbers=_tr(0x8FC, 4), ptype="base", pnum=1, trans0=True),
    "ipotion":          dict(width=2, numbers=_tr(0x9FC, 4), ptype="base", pnum=1, trans0=True),
    "ppotion":          dict(width=2, numbers=_tr(0x20FC, 4), ptype="base", pnum=1, trans0=True),
    "shieldpotion":     dict(width=2, numbers=_tr(0x11FC, 4), ptype="base", pnum=1, trans0=True),
    "speedpotion":      dict(width=2, numbers=_tr(0x12FC, 4), ptype="base", pnum=1, trans0=True),
    "magicpotion":      dict(width=2, numbers=_tr(0x13FC, 4), ptype="base", pnum=1, trans0=True),
    "shotpowerpotion":  dict(width=2, numbers=_tr(0x14FC, 4), ptype="base", pnum=1, trans0=True),
    "shotspeedpotion":  dict(width=2, numbers=_tr(0x15FC, 4), ptype="base", pnum=1, trans0=True),
    "fightpotion":      dict(width=2, numbers=_tr(0x16FC, 4), ptype="base", pnum=1, trans0=True),
    "invis":            dict(width=3, numbers=_tr(0x1700, 9), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "transportability": dict(width=2, numbers=_tr(0x23FC, 4), ptype="base", pnum=1, trans0=True),
    "reflect":          dict(width=2, numbers=_tr(0x24FC, 4), ptype="base", pnum=1, trans0=True),
    "repulse":          dict(width=2, numbers=_tr(0x26FC, 4), ptype="base", pnum=1, trans0=True),
    "invuln":           dict(width=2, numbers=_tr(0x2784, 4), ptype="base", pnum=1, trans0=True),
    "supershot":        dict(width=2, numbers=_tr(0x2788, 4), ptype="base", pnum=1, trans0=True),
    "pushwall":         dict(width=3, numbers=_tr(0x20F6, 6), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "treasure":         dict(width=3, numbers=_tr(0x987, 9), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "treasurelocked":   dict(width=3, numbers=_tr(0x25E4, 9), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "goldbag":          dict(width=3, numbers=_tr(0x9A2, 9), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "tport":            dict(width=2, numbers=_tr(0x49E, 4), ptype="teleff", pnum=0, trans0=True),
    "ff":               dict(width=2, numbers=_tr(0x4A2, 4), ptype="teleff", pnum=0, trans0=True),
    "exit":             dict(width=2, numbers=[0x39E, 0x39F, 0x6, 0x6], ptype="floor", pnum=0, trans0=False),
    "exit4":            dict(width=2, numbers=_tr(0xCFC, 4), ptype="floor", pnum=0, trans0=False),
    "exit6":            dict(width=2, numbers=_tr(0x39E, 4), ptype="floor", pnum=0, trans0=False),
    "exit8":            dict(width=2, numbers=_tr(0xDFC, 4), ptype="floor", pnum=0, trans0=False),
    "vdoor":            dict(width=2, numbers=_tr(0x1D80, 4), ptype="base", pnum=0, trans0=True),
    "hdoor":            dict(width=2, numbers=_tr(0x1D48, 4), ptype="base", pnum=0, trans0=True),
    "plus":             dict(width=2, numbers=_tr(0xBFC, 4), ptype="base", pnum=1, trans0=True),
    "dragon":           dict(width=4, numbers=_tr(0x2100, 16), ptype="base", pnum=8, trans0=True, nudgex=0, nudgey=-16),
    "generator1":       dict(width=3, numbers=_tr(0x9C6, 9), ptype="base", pnum=5, trans0=True, nudgex=-4, nudgey=-4),
    "generator2":       dict(width=3, numbers=_tr(0x9CF, 9), ptype="base", pnum=5, trans0=True, nudgex=-4, nudgey=-4),
    "generator3":       dict(width=3, numbers=_tr(0x9D8, 9), ptype="base", pnum=5, trans0=True, nudgex=-4, nudgey=-4),
    "ghostgen1":        dict(width=3, numbers=_tr(0x9AB, 9), ptype="base", pnum=5, trans0=True, nudgex=-4, nudgey=-4),
    "ghostgen2":        dict(width=3, numbers=_tr(0x9B4, 9), ptype="base", pnum=5, trans0=True, nudgex=-4, nudgey=-4),
    "ghostgen3":        dict(width=3, numbers=_tr(0x9BD, 9), ptype="base", pnum=5, trans0=True, nudgex=-4, nudgey=-4),
    "ghost":            dict(width=3, numbers=_tr(0x800, 9), ptype="base", pnum=4, trans0=True, nudgex=-4, nudgey=-4),
    "grunt":            dict(width=3, numbers=_tr(0x9E1, 9), ptype="base", pnum=4, trans0=True, nudgex=-4, nudgey=-4),
    "demon":            dict(width=3, numbers=_tr(0x183F, 9), ptype="base", pnum=8, trans0=True, nudgex=-4, nudgey=-4),
    "lobber":           dict(width=3, numbers=_tr(0x1B57, 6), ptype="base", pnum=11, trans0=True, nudgex=-4, nudgey=-4),
    "sorcerer":         dict(width=3, numbers=_tr(0x13A2, 9), ptype="base", pnum=11, trans0=True, nudgex=-4, nudgey=-4),
    "auxgrunt":         dict(width=3, numbers=_tr(0x9E1, 9), ptype="base", pnum=4, trans0=True, nudgex=-4, nudgey=-4),
    "death":            dict(width=3, numbers=_tr(0x1A75, 9), ptype="base", pnum=0, trans0=True, nudgex=-4, nudgey=-4),
    "acid":             dict(width=3, numbers=_tr(0x2300, 9), ptype="base", pnum=1, trans0=True, nudgex=-4, nudgey=-4),
    "supersorc":        dict(width=3, numbers=_tr(0x13A2, 9), ptype="base", pnum=11, trans0=True, nudgex=-4, nudgey=-4),
    "it":               dict(width=3, numbers=_tr(0x2600, 9), ptype="base", pnum=8, trans0=True, nudgex=-4, nudgey=-4),
    "arrowleft":        dict(width=2, numbers=[0, 0x1C8F, 0, 0x1C91], ptype="elf", pnum=1, trans0=True),
    "arrowright":       dict(width=2, numbers=[0x1C7D, 0, 0x1C7F, 0], ptype="elf", pnum=1, trans0=True),
    "arrowup":          dict(width=2, numbers=[0, 0, 0x1C74, 0x1C75], ptype="elf", pnum=1, trans0=True),
    "arrowdown":        dict(width=2, numbers=[0x1C86, 0x1C87, 0, 0], ptype="elf", pnum=1, trans0=True),
}


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


RE_ITEM_TYPE = re.compile(r"^(key)$")


def doitem(arg: str, output: str) -> None:
    split = arg.split("-")
    item_type = ""

    for ss in split:
        m = RE_ITEM_TYPE.match(ss)
        if m:
            item_type = m.group(1)

    stamp = item_get_stamp(item_type)
    height = len(stamp.numbers) // stamp.width
    img = blank_image(8 * stamp.width, 8 * height)
    write_stamp_to_image(img, stamp, 0, 0)
    save_to_png(output, img)

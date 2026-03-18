#!/usr/bin/env python3
"""gex -- Gauntlet II tile/stamp/maze extractor.

A Python port of the Go-based gex tool for extracting and rendering
tiles, stamps, floors, walls, items, monsters, and mazes from
Gauntlet II arcade ROMs.
"""

from __future__ import annotations

import argparse
import sys
from enum import IntEnum

from .render import gen_image, save_to_png


class RunType(IntEnum):
    NONE = 0
    MONSTER = 1
    FLOOR = 2
    WALL = 3
    ITEM = 4
    MAZE = 5


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        prog="gex",
        description="Gauntlet II tile/stamp/maze extractor",
    )
    parser.add_argument("-a", "--animate", action="store_true", help="Animate monster")
    parser.add_argument("--pt", default="base", help="Palette type")
    parser.add_argument("--pn", default="0", help="Palette number (in hex)")
    parser.add_argument("-t", "--tile", default="0", help="Tile number to render (in hex)")
    parser.add_argument("-x", type=int, default=2, help="X dimension, in tiles")
    parser.add_argument("-y", type=int, default=2, help="Y dimension, in tiles")
    parser.add_argument("-o", "--output", default="output.png", help="Output file")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("args", nargs="*", help="Command arguments (e.g. maze0, item-key, ghost-walk-up)")
    return parser.parse_known_args()


def main() -> None:
    opts, extra = parse_args()

    tile = int(opts.tile, 16)
    pal_num = int(opts.pn, 16)
    pal_type = opts.pt
    args = opts.args + extra

    run_type = RunType.NONE
    if args:
        arg = args[0]
        if arg.startswith("ghost"):
            run_type = RunType.MONSTER
        elif arg.startswith("floor"):
            run_type = RunType.FLOOR
        elif arg.startswith("wall"):
            run_type = RunType.WALL
        elif arg.startswith("item"):
            run_type = RunType.ITEM
        elif arg.startswith("maze"):
            run_type = RunType.MAZE

    if run_type == RunType.NONE:
        if tile:
            img = gen_image(tile, opts.x, opts.y, pal_type, pal_num)
            save_to_png(opts.output, img)
        else:
            print("Missing or incorrect identity line.")
            sys.exit(1)
    elif run_type == RunType.FLOOR:
        from .floor import dofloor
        dofloor(args[0], opts.output)
    elif run_type == RunType.WALL:
        from .wall import dowall
        dowall(args[0], opts.output)
    elif run_type == RunType.MONSTER:
        from .monsters import domonster
        domonster(args[0], opts.output, pal_type, pal_num, opts.animate)
    elif run_type == RunType.ITEM:
        from .items import doitem
        doitem(args[0], opts.output)
    elif run_type == RunType.MAZE:
        from .maze import domaze
        domaze(args[0], opts.output, opts.verbose)

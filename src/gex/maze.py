"""Maze CLI handler and metadata printing."""

from __future__ import annotations

import re

from .constants import LFLAG3_RANDOMFOOD_MASK, MAZE_FLAG_STRINGS, MAZE_SECRET_STRINGS
from .mazedecode import Maze, maze_decompress
from .roms import slapstic_read_maze


def maze_meta_print(maze: Maze) -> None:
    print(f"  Encoded length: {maze.encodedbytes:3d} bytes")
    print(
        f"  Wall pattern: {maze.wallpattern:02d}, Wall color: {maze.wallcolor:02d}"
        f"     Floor pattern: {maze.floorpattern:02d}, Floor color: {maze.floorcolor:02d}"
    )
    flags_str = " ".join(
        v for k, v in MAZE_FLAG_STRINGS.items() if (maze.flags & k) != 0
    )
    print(f"  Flags: {flags_str}")
    print(f"  Random food adds: {(maze.flags & LFLAG3_RANDOMFOOD_MASK) >> 8}")
    print(f"  Secret trick: {maze.secret:2d} - {MAZE_SECRET_STRINGS.get(maze.secret, '???')}")


RE_MAZE_NUM = re.compile(r"^maze(\d+)")
RE_MAZE_META = re.compile(r"^meta$")


def domaze(arg: str, output: str, verbose: bool) -> None:
    split = arg.split("-")
    maze_num = -1
    maze_meta = 0

    for ss in split:
        m = RE_MAZE_NUM.match(ss)
        if m:
            maze_num = int(m.group(1))
            if maze_num < 0 or maze_num > 117:
                raise ValueError("Invalid maze number specified.")
            continue
        if RE_MAZE_META.match(ss):
            maze_meta = 1

    print(f"Maze number: {maze_num}")
    maze = maze_decompress(slapstic_read_maze(maze_num), maze_meta > 0)

    if verbose or maze_meta > 0:
        maze_meta_print(maze)

    if maze_meta == 0:
        from .pfrender import genpfimage
        genpfimage(maze, output)

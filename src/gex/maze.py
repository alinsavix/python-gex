"""Maze CLI handler and metadata printing."""

from __future__ import annotations

from .constants import LFLAG3_RANDOMFOOD_MASK, MAZE_FLAG_STRINGS, MAZE_SECRET_STRINGS, MAX_MAZE_NUM
from .mazedecode import Maze, maze_decompress
from .roms import slapstic_read_maze


def maze_meta_print(maze: Maze) -> None:
    print(f"  Encoded length: {maze.encodedbytes:3d} bytes")
    print(
        f"  Wall pattern: {maze.wallpattern:02d}, Wall color: {maze.wallcolor:02d}"
        f"     Floor pattern: {maze.floorpattern:02d}, Floor color: {maze.floorcolor:02d}"
    )
    flags_str = " ".join(
        v for k, v in MAZE_FLAG_STRINGS.items() if maze.flags & k
    )
    print(f"  Flags: {flags_str}")
    print(f"  Random food adds: {(maze.flags & LFLAG3_RANDOMFOOD_MASK) >> 8}")
    print(f"  Secret trick: {maze.secret:2d} - {MAZE_SECRET_STRINGS.get(maze.secret, '???')}")


def domaze(arg: str, output: str, verbose: bool) -> None:
    split = arg.split("-")
    maze_num = -1
    maze_meta = False

    for ss in split:
        if ss.startswith("maze") and ss[4:].isdigit():
            maze_num = int(ss[4:])
            if maze_num < 0 or maze_num > MAX_MAZE_NUM:
                raise ValueError("Invalid maze number specified.")
        elif ss == "meta":
            maze_meta = True

    print(f"Maze number: {maze_num}")
    maze = maze_decompress(slapstic_read_maze(maze_num), maze_meta)

    if verbose or maze_meta:
        maze_meta_print(maze)

    if not maze_meta:
        from .pfrender import genpfimage
        genpfimage(maze, output)

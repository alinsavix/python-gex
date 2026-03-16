"""Maze decompression algorithm."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

from .constants import MazeObjIds
from .rand import SeededRandom

# Module-level PRNG instance shared with pfrender and wall
gorand: SeededRandom = SeededRandom(5)


@dataclass
class Maze:
    data: dict[tuple[int, int], int] = field(default_factory=dict)
    encodedbytes: int = 0
    secret: int = 0
    flags: int = 0
    wallpattern: int = 0
    wallcolor: int = 0
    floorpattern: int = 0
    floorcolor: int = 0


def index2xy(index: int) -> tuple[int, int]:
    if index < 0:
        raise ValueError(f"Coordinates requested for index < 0: {index}")
    y = index // 32
    x = index - (y * 32)
    return x, y


def iswall(t: int) -> bool:
    return t in (
        MazeObjIds.WALL_REGULAR, MazeObjIds.WALL_SECRET, MazeObjIds.WALL_DESTRUCTABLE,
        MazeObjIds.WALL_RANDOM, MazeObjIds.WALL_TRAPCYC1, MazeObjIds.WALL_TRAPCYC2,
        MazeObjIds.WALL_TRAPCYC3,
    )


def isspecialfloor(t: int) -> bool:
    return t in (
        MazeObjIds.TILE_STUN, MazeObjIds.TILE_TRAP1, MazeObjIds.TILE_TRAP2,
        MazeObjIds.TILE_TRAP3, MazeObjIds.EXIT, MazeObjIds.EXITTO6,
        MazeObjIds.TRANSPORTER,
    )


def expand(maze: Maze, location: int, t: int, count: int) -> int:
    if t == MazeObjIds.TILE_FLOOR:
        return location + count

    i = 0
    while i < count:
        x, y = index2xy(location + i)
        maze.data[(x, y)] = t
        if t == MazeObjIds.MONST_DRAGON:
            i += 1  # extra increment matching Go's in-loop i++
        i += 1
    return location + count


def vexpand(maze: Maze, location: int, t: int, count: int) -> int:
    if t == MazeObjIds.TILE_FLOOR:
        return location + 1

    for i in range(count):
        x, y = index2xy(location - (i * 32))
        maze.data[(x, y)] = t

    return location + 1


def maze_decompress(compressed: list[int], metaonly: bool = False) -> Maze:
    global gorand
    gorand = SeededRandom(5)
    maze = Maze()
    maze.encodedbytes = len(compressed)
    maze.secret = compressed[0] & 0x1F

    flagbytes = bytes([compressed[1], compressed[2], compressed[3], compressed[4]])
    maze.flags = struct.unpack(">I", flagbytes)[0]

    maze.wallpattern = compressed[5] & 0x0F
    maze.floorpattern = (compressed[5] & 0xF0) >> 4
    maze.wallcolor = compressed[6] & 0x0F
    maze.floorcolor = (compressed[6] & 0xF0) >> 4

    if metaonly:
        return maze

    htype1 = compressed[7]
    htype2 = compressed[8]
    vtype1 = compressed[9]
    vtype2 = compressed[10]
    prev = htype2

    # Fill first row with walls
    for i in range(32):
        maze.data[(i, 0)] = MazeObjIds.WALL_REGULAR

    location = 32
    compressed = compressed[11:]

    while location < 1024:
        if compressed[0] == 0:
            print("WARNING: Read end of maze datastream before maze full.")
            break

        token = compressed[0]
        compressed = compressed[1:]
        count = (token & 0x0F) + 1
        longcount = (token & 0x1F) + 1

        top2 = token & 0xC0
        if top2 == 0x00:
            # Place one literal object
            location = expand(maze, location, token & 0x3F, 1)
            prev = token

        elif top2 == 0x40:
            # Repeat special type
            sub = token & 0x30
            if sub == 0x00:
                prev = htype1
            elif sub == 0x10:
                prev = vtype1
            elif sub == 0x20:
                prev = htype2
            elif sub == 0x30:
                prev = vtype2

            previtem = prev & 0x3F
            prevtop = prev & 0xC0

            if prevtop == 0x00:
                if (token & 0x10) != 0:
                    location = vexpand(maze, location, previtem, count)
                else:
                    location = expand(maze, location, previtem, count)
            elif prevtop == 0x40:
                location = expand(maze, location, MazeObjIds.TILE_FLOOR, count)
                location = expand(maze, location, previtem, 1)
            elif prevtop == 0x80:
                location = expand(maze, location, previtem, 1)
                location = expand(maze, location, MazeObjIds.TILE_FLOOR, count)
            elif prevtop == 0xC0:
                location = expand(maze, location, MazeObjIds.WALL_REGULAR, count)
                location = expand(maze, location, previtem, 1)

        elif top2 == 0x80:
            if (token & 0x20) != 0:
                if (token & 0x10) != 0:
                    location = vexpand(maze, location, MazeObjIds.WALL_REGULAR, count)
                else:
                    location = expand(maze, location, MazeObjIds.WALL_REGULAR, count)
            else:
                location = expand(maze, location, prev & 0x3F, longcount)

        elif top2 == 0xC0:
            if (token & 0x20) != 0:
                location = expand(maze, location, MazeObjIds.TILE_FLOOR, longcount)
                location = expand(maze, location, MazeObjIds.WALL_REGULAR, 1)
            else:
                location = expand(maze, location, MazeObjIds.TILE_FLOOR, longcount)

    if len(compressed) != 1 or compressed[0] != 0:
        print(f"WARNING: Incomplete maze decode? ({len(compressed)} bytes remaining)")

    return maze

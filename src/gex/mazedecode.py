"""Maze decompression algorithm."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

from .constants import MazeObjIds
from .rand import SeededRandom

# Bit masks for compressed token bytes
_TOP2_MASK   = 0xC0  # top 2 bits identify the token class
_OBJ_MASK    = 0x3F  # bottom 6 bits: literal object ID
_COUNT4_MASK = 0x0F  # bottom 4 bits: repeat count (minus 1)
_COUNT5_MASK = 0x1F  # bottom 5 bits: long repeat count (minus 1)
_SUB_MASK    = 0x30  # bits 4-5: sub-type selector within TOK_REPEAT

# Token classes (top 2 bits of each token byte)
_TOK_LITERAL      = 0x00  # place one literal object
_TOK_REPEAT       = 0x40  # repeat a special typed object
_TOK_WALL_OR_PREV = 0x80  # place walls or repeat prev object
_TOK_FLOOR        = 0xC0  # place a run of floor tiles

# Sub-types for TOK_REPEAT: bits 4-5 select which "prev context" to use
_SUB_HTYPE1 = 0x00
_SUB_VTYPE1 = 0x10
_SUB_HTYPE2 = 0x20
_SUB_VTYPE2 = 0x30


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
    rand: SeededRandom = field(default_factory=lambda: SeededRandom(5))


def index2xy(index: int) -> tuple[int, int]:
    if index < 0:
        raise ValueError(f"Coordinates requested for index < 0: {index}")
    return index % 32, index // 32


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

    step = 2 if t == MazeObjIds.MONST_DRAGON else 1
    for i in range(0, count, step):
        x, y = index2xy(location + i)
        maze.data[(x, y)] = t
    return location + count


def vexpand(maze: Maze, location: int, t: int, count: int) -> int:
    if t == MazeObjIds.TILE_FLOOR:
        return location + 1

    for i in range(count):
        x, y = index2xy(location - (i * 32))
        maze.data[(x, y)] = t

    return location + 1


def _token_literal(maze: Maze, location: int, token: int) -> tuple[int, int]:
    """TOK_LITERAL: place one literal object; new prev = token."""
    location = expand(maze, location, token & _OBJ_MASK, 1)
    return location, token


_SUB_TO_CTX = {_SUB_HTYPE1: 0, _SUB_VTYPE1: 1, _SUB_HTYPE2: 2, _SUB_VTYPE2: 3}


def _token_repeat(
    maze: Maze, location: int, token: int, prev: int,
    htype1: int, htype2: int, vtype1: int, vtype2: int,
) -> tuple[int, int]:
    """TOK_REPEAT: repeat a special typed object.

    Bits 4-5 of the token select which context type (htype1/vtype1/htype2/vtype2)
    becomes the new prev.  The top 2 bits of *prev* then determine the repeat mode.
    """
    count = (token & _COUNT4_MASK) + 1
    ctx_types = [htype1, vtype1, htype2, vtype2]
    prev = ctx_types[_SUB_TO_CTX[token & _SUB_MASK]]

    previtem = prev & _OBJ_MASK
    prevtop  = prev & _TOP2_MASK

    if prevtop == _TOK_LITERAL:
        # prev was a literal: repeat it horizontally or vertically
        if token & _SUB_VTYPE1:
            location = vexpand(maze, location, previtem, count)
        else:
            location = expand(maze, location, previtem, count)
    elif prevtop == _TOK_REPEAT:
        # prev was a repeat: floor run, then one previtem
        location = expand(maze, location, MazeObjIds.TILE_FLOOR, count)
        location = expand(maze, location, previtem, 1)
    elif prevtop == _TOK_WALL_OR_PREV:
        # prev was wall-or-prev: one previtem, then floor run
        location = expand(maze, location, previtem, 1)
        location = expand(maze, location, MazeObjIds.TILE_FLOOR, count)
    elif prevtop == _TOK_FLOOR:
        # prev was floor: wall run, then one previtem
        location = expand(maze, location, MazeObjIds.WALL_REGULAR, count)
        location = expand(maze, location, previtem, 1)

    return location, prev


def _token_wall_or_prev(maze: Maze, location: int, token: int, prev: int) -> int:
    """TOK_WALL_OR_PREV: place walls or repeat prev object.

    Bit 5 set → wall run; bit 4 set within that → vertical.
    Bit 5 clear → repeat prev object (5-bit count).
    """
    count     = (token & _COUNT4_MASK) + 1
    longcount = (token & _COUNT5_MASK) + 1
    if token & 0x20:
        if token & 0x10:
            location = vexpand(maze, location, MazeObjIds.WALL_REGULAR, count)
        else:
            location = expand(maze, location, MazeObjIds.WALL_REGULAR, count)
    else:
        location = expand(maze, location, prev & _OBJ_MASK, longcount)
    return location


def _token_floor(maze: Maze, location: int, token: int) -> int:
    """TOK_FLOOR: place a run of floor tiles, optionally capped with a wall."""
    longcount = (token & _COUNT5_MASK) + 1
    location = expand(maze, location, MazeObjIds.TILE_FLOOR, longcount)
    if token & 0x20:
        location = expand(maze, location, MazeObjIds.WALL_REGULAR, 1)
    return location


def maze_decompress(compressed: list[int], metaonly: bool = False) -> Maze:
    maze = Maze()
    maze.encodedbytes = len(compressed)
    maze.secret = compressed[0] & 0x1F

    maze.flags = struct.unpack(">I", bytes(compressed[1:5]))[0]

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
    maze.data.update({(i, 0): MazeObjIds.WALL_REGULAR for i in range(32)})

    location = 32
    pos = 11
    end = len(compressed)

    while location < 1024:
        if pos >= end or compressed[pos] == 0:
            print("WARNING: Read end of maze datastream before maze full.")
            break

        token = compressed[pos]
        pos += 1

        top2 = token & _TOP2_MASK
        if top2 == _TOK_LITERAL:
            location, prev = _token_literal(maze, location, token)
        elif top2 == _TOK_REPEAT:
            location, prev = _token_repeat(maze, location, token, prev, htype1, htype2, vtype1, vtype2)
        elif top2 == _TOK_WALL_OR_PREV:
            location = _token_wall_or_prev(maze, location, token, prev)
        elif top2 == _TOK_FLOOR:
            location = _token_floor(maze, location, token)

    remaining = end - pos
    if remaining != 1 or compressed[pos] != 0:
        print(f"WARNING: Incomplete maze decode? ({remaining} bytes remaining)")

    return maze

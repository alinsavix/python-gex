"""Adjacency helpers for maze objects: walls, doors, and forcefields."""

from __future__ import annotations

from typing import Callable

from .constants import LFLAG4_WRAP_H, LFLAG4_WRAP_V, MazeObjIds
from .mazedecode import Maze, iswall


def whatis(maze: Maze, x: int, y: int) -> int:
    return maze.data.get((x, y), 0)


def isdoor(t: int) -> bool:
    return t in (MazeObjIds.DOOR_HORIZ, MazeObjIds.DOOR_VERT)


def isforcefield(t: int) -> bool:
    return t == MazeObjIds.FORCEFIELDHUB


def copyedges(maze: Maze) -> None:
    if not maze.flags & LFLAG4_WRAP_H:
        maze.data.update({(32, i): maze.data.get((0, i), 0) for i in range(33)})
    if not maze.flags & LFLAG4_WRAP_V:
        maze.data.update({(i, 32): maze.data.get((i, 0), 0) for i in range(33)})


_WALLADJ3_CHECKS = [(-1, 0, 4), (0, 1, 16), (-1, 1, 8)]
_WALLADJ8_CHECKS = [
    (-1, -1, 0x01), (0, -1, 0x02), (1, -1, 0x04),
    (-1,  0, 0x08),                (1,  0, 0x10),
    (-1,  1, 0x20), (0,  1, 0x40), (1,  1, 0x80),
]
_DOORADJ4_CHECKS = [(0, -1, 0x01), (1, 0, 0x02), (0, 1, 0x04), (-1, 0, 0x08)]


def check_adjacency(
    maze: Maze, x: int, y: int,
    checks: list[tuple[int, int, int]],
    predicate: Callable[[int], bool],
) -> int:
    return sum(val for dx, dy, val in checks if predicate(whatis(maze, x + dx, y + dy)))


def checkwalladj3(maze: Maze, x: int, y: int) -> int:
    return check_adjacency(maze, x, y, _WALLADJ3_CHECKS, iswall)


def checkwalladj8(maze: Maze, x: int, y: int) -> int:
    return check_adjacency(maze, x, y, _WALLADJ8_CHECKS, iswall)


def checkdooradj4(maze: Maze, x: int, y: int) -> int:
    return check_adjacency(maze, x, y, _DOORADJ4_CHECKS, isdoor)


FF_LOOP_DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
ADJ_VALUES = [0x01, 0x02, 0x04, 0x08]


def checkffadj4(maze: Maze, x: int, y: int) -> int:
    adj = 0
    for (dx, dy), adj_val in zip(FF_LOOP_DIRS, ADJ_VALUES):
        for j in range(1, 16):
            t = whatis(maze, x + j * dx, y + j * dy)
            if j > 1 and isforcefield(t):
                adj += adj_val
                break
            elif iswall(t):
                break
    return adj


FFMap = set[tuple[int, int]]


def ff_mark(ffmap: FFMap, maze: Maze, x: int, y: int, direction: int) -> None:
    dx, dy = FF_LOOP_DIRS[direction]
    for i in range(1, 33):
        nx = x + dx * i
        ny = y + dy * i
        if isforcefield(maze.data.get((nx, ny), 0)):
            return
        ffmap.add((nx, ny))


def ff_make_map(maze: Maze) -> FFMap:
    ffmap: FFMap = set()
    for (kx, ky), v in maze.data.items():
        if not isforcefield(v):
            continue
        adj = checkffadj4(maze, kx, ky)
        if adj & 0x02:
            ff_mark(ffmap, maze, kx, ky, 1)
        if adj & 0x04:
            ff_mark(ffmap, maze, kx, ky, 2)
    return ffmap

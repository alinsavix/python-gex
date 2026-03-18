"""Playfield rendering -- generates full maze images."""

from __future__ import annotations

import dataclasses

from PIL import Image

from .constants import (
    LFLAG4_WRAP_H, LFLAG4_WRAP_V, MazeObjIds,
)
from .door import DOOR_HORIZ, DOOR_VERT, door_get_stamp
from .floor import floor_get_stamp
from .items import item_get_stamp
from .mazedecode import Maze, iswall, isspecialfloor
from .palettes import IRGB, palette_make_special
from .render import Stamp, blank_image, write_stamp_to_image, save_to_png
from .wall import wall_get_stamp, wall_get_destructable_stamp, ff_get_stamp


FOODS = ["ifood1", "ifood2", "ifood3"]

# ---------------------------------------------------------------------------
# Dispatch tables
# ---------------------------------------------------------------------------

# Objects that map directly to a named item stamp.
_ITEM_STAMP_NAMES: dict[int, str] = {
    MazeObjIds.WALL_MOVABLE:      "pushwall",
    MazeObjIds.KEY:               "key",
    MazeObjIds.POWER_INVIS:       "invis",
    MazeObjIds.POWER_REPULSE:     "repulse",
    MazeObjIds.POWER_REFLECT:     "reflect",
    MazeObjIds.POWER_TRANSPORT:   "transportability",
    MazeObjIds.POWER_SUPERSHOT:   "supershot",
    MazeObjIds.POWER_INVULN:      "invuln",
    MazeObjIds.PLAYERSTART:       "plus",
    MazeObjIds.EXIT:              "exit",
    MazeObjIds.EXITTO6:           "exit6",
    MazeObjIds.MONST_GHOST:       "ghost",
    MazeObjIds.MONST_GRUNT:       "grunt",
    MazeObjIds.MONST_DEMON:       "demon",
    MazeObjIds.MONST_LOBBER:      "lobber",
    MazeObjIds.MONST_SORC:        "sorcerer",
    MazeObjIds.MONST_AUX_GRUNT:   "auxgrunt",
    MazeObjIds.MONST_DEATH:       "death",
    MazeObjIds.MONST_ACID:        "acid",
    MazeObjIds.MONST_SUPERSORC:   "supersorc",
    MazeObjIds.MONST_IT:          "it",
    MazeObjIds.MONST_DRAGON:      "dragon",
    MazeObjIds.GEN_GHOST1:        "ghostgen1",
    MazeObjIds.GEN_GHOST2:        "ghostgen2",
    MazeObjIds.GEN_GHOST3:        "ghostgen3",
    MazeObjIds.GEN_GRUNT1:        "generator1",
    MazeObjIds.GEN_DEMON1:        "generator1",
    MazeObjIds.GEN_LOBBER1:       "generator1",
    MazeObjIds.GEN_SORC1:         "generator1",
    MazeObjIds.GEN_AUX_GRUNT1:    "generator1",
    MazeObjIds.GEN_GRUNT2:        "generator2",
    MazeObjIds.GEN_DEMON2:        "generator2",
    MazeObjIds.GEN_LOBBER2:       "generator2",
    MazeObjIds.GEN_SORC2:         "generator2",
    MazeObjIds.GEN_AUX_GRUNT2:    "generator2",
    MazeObjIds.GEN_GRUNT3:        "generator3",
    MazeObjIds.GEN_DEMON3:        "generator3",
    MazeObjIds.GEN_LOBBER3:       "generator3",
    MazeObjIds.GEN_SORC3:         "generator3",
    MazeObjIds.GEN_AUX_GRUNT3:    "generator3",
    MazeObjIds.TREASURE:          "treasure",
    MazeObjIds.TREASURE_LOCKED:   "treasurelocked",
    MazeObjIds.TREASURE_BAG:      "goldbag",
    MazeObjIds.FOOD_DESTRUCTABLE: "food",
    MazeObjIds.POT_DESTRUCTABLE:  "potion",
    MazeObjIds.POT_INVULN:        "ipotion",
    MazeObjIds.TRANSPORTER:       "tport",
}

# Floor-tile objects that use a palette override: obj → (ptype, dots)
_FLOOR_TILE_INFO: dict[int, tuple[str, int]] = {
    MazeObjIds.TILE_STUN:  ("stun", 0),
    MazeObjIds.TILE_TRAP1: ("trap", 1),
    MazeObjIds.TILE_TRAP2: ("trap", 2),
    MazeObjIds.TILE_TRAP3: ("trap", 3),
}

# Wall-tile objects that use wall_get_stamp: obj → dots
_WALL_TILE_DOTS: dict[int, int] = {
    MazeObjIds.WALL_REGULAR:   0,
    MazeObjIds.WALL_TRAPCYC1:  1,
    MazeObjIds.WALL_TRAPCYC2:  2,
    MazeObjIds.WALL_TRAPCYC3:  3,
    MazeObjIds.WALL_RANDOM:    4,
}


def whatis(maze: Maze, x: int, y: int) -> int:
    return maze.data.get((x, y), 0)


def isdoor(t: int) -> bool:
    return t in (MazeObjIds.DOOR_HORIZ, MazeObjIds.DOOR_VERT)


def isforcefield(t: int) -> bool:
    return t == MazeObjIds.FORCEFIELDHUB


def copyedges(maze: Maze) -> None:
    for i in range(33):
        if (maze.flags & LFLAG4_WRAP_H) == 0:
            maze.data[(32, i)] = maze.data.get((0, i), 0)
    for i in range(33):
        if (maze.flags & LFLAG4_WRAP_V) == 0:
            maze.data[(i, 32)] = maze.data.get((i, 0), 0)


def checkwalladj3(maze: Maze, x: int, y: int) -> int:
    adj = 0
    if iswall(whatis(maze, x - 1, y)):
        adj += 4
    if iswall(whatis(maze, x, y + 1)):
        adj += 16
    if iswall(whatis(maze, x - 1, y + 1)):
        adj += 8
    return adj


def checkwalladj8(maze: Maze, x: int, y: int) -> int:
    adj = 0
    if iswall(whatis(maze, x - 1, y - 1)):
        adj += 0x01
    if iswall(whatis(maze, x, y - 1)):
        adj += 0x02
    if iswall(whatis(maze, x + 1, y - 1)):
        adj += 0x04
    if iswall(whatis(maze, x - 1, y)):
        adj += 0x08
    if iswall(whatis(maze, x + 1, y)):
        adj += 0x10
    if iswall(whatis(maze, x - 1, y + 1)):
        adj += 0x20
    if iswall(whatis(maze, x, y + 1)):
        adj += 0x40
    if iswall(whatis(maze, x + 1, y + 1)):
        adj += 0x80
    return adj


def checkdooradj4(maze: Maze, x: int, y: int) -> int:
    adj = 0
    if isdoor(whatis(maze, x, y - 1)):
        adj += 0x01
    if isdoor(whatis(maze, x + 1, y)):
        adj += 0x02
    if isdoor(whatis(maze, x, y + 1)):
        adj += 0x04
    if isdoor(whatis(maze, x - 1, y)):
        adj += 0x08
    return adj


FF_LOOP_DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
ADJ_VALUES = [0x01, 0x02, 0x04, 0x08]


def checkffadj4(maze: Maze, x: int, y: int) -> int:
    adj = 0
    for i in range(4):
        for j in range(1, 16):
            dx, dy = FF_LOOP_DIRS[i]
            t = whatis(maze, x + j * dx, y + j * dy)
            if j > 1 and isforcefield(t):
                adj += ADJ_VALUES[i]
                break
            elif iswall(t):
                break
    return adj


FFMap = dict[tuple[int, int], bool]


def ff_mark(ffmap: FFMap, maze: Maze, x: int, y: int, direction: int) -> None:
    dx, dy = FF_LOOP_DIRS[direction]
    for i in range(1, 33):
        nx = x + dx * i
        ny = y + dy * i
        if isforcefield(maze.data.get((nx, ny), 0)):
            return
        ffmap[(nx, ny)] = True


def ff_make_map(maze: Maze) -> FFMap:
    ffmap: FFMap = {}
    for (kx, ky), v in maze.data.items():
        if not isforcefield(v):
            continue
        adj = checkffadj4(maze, kx, ky)
        if (adj & 0x02) > 0:
            ff_mark(ffmap, maze, kx, ky, 1)
        if (adj & 0x04) > 0:
            ff_mark(ffmap, maze, kx, ky, 2)
    return ffmap


def dotat(img: Image.Image, xloc: int, yloc: int) -> None:
    c = IRGB(0xFFFF).to_rgba()
    pixels = img.load()
    w, h = img.size
    for y in range(2):
        for x in range(2):
            px, py = xloc + x, yloc + y
            if 0 <= px < w and 0 <= py < h:
                pixels[px, py] = c


def renderdots(img: Image.Image, xloc: int, yloc: int, count: int) -> None:
    if count == 1:
        dotat(img, xloc + 7, yloc + 7)
    elif count == 2:
        dotat(img, xloc + 9, yloc + 5)
        dotat(img, xloc + 5, yloc + 9)
    elif count == 3:
        dotat(img, xloc + 7, yloc + 7)
        dotat(img, xloc + 9, yloc + 5)
        dotat(img, xloc + 5, yloc + 9)
    elif count == 4:
        dotat(img, xloc + 9, yloc + 5)
        dotat(img, xloc + 5, yloc + 9)
        dotat(img, xloc + 5, yloc + 5)
        dotat(img, xloc + 9, yloc + 9)


def genpfimage(maze: Maze, output: str) -> None:
    extrax = 16 if (maze.flags & LFLAG4_WRAP_H) == 0 else 0
    extray = 16 if (maze.flags & LFLAG4_WRAP_V) == 0 else 0

    img = blank_image(8 * 2 * 32 + 32 + extrax, 8 * 2 * 32 + 32 + extray)

    ffmap = ff_make_map(maze)
    copyedges(maze)
    palette_make_special(maze.floorpattern, maze.floorcolor, maze.wallpattern, maze.wallcolor)

    # Draw floor tiles
    for y in range(32):
        for x in range(32):
            adj = 0
            if maze.wallpattern < 11:
                adj = checkwalladj3(maze, x, y)
            stamp = floor_get_stamp(maze.floorpattern, adj + maze.rand.intn(4), maze.floorcolor)
            if ffmap.get((x, y), False):
                stamp = dataclasses.replace(stamp, ptype="forcefield", pnum=0)
            write_stamp_to_image(img, stamp, x * 16 + 16, y * 16 + 16)

    lastx = 32 if (maze.flags & LFLAG4_WRAP_H) == 0 else 31
    lasty = 32 if (maze.flags & LFLAG4_WRAP_V) == 0 else 31

    # Draw objects on top of floors
    for y in range(lasty + 1):
        for x in range(lastx + 1):
            stamp = None
            dots = 0
            obj = whatis(maze, x, y)

            if obj == MazeObjIds.TILE_FLOOR:
                pass

            elif obj in _FLOOR_TILE_INFO:
                ptype_override, dots = _FLOOR_TILE_INFO[obj]
                adj = checkwalladj3(maze, x, y) + maze.rand.intn(4)
                stamp = dataclasses.replace(
                    floor_get_stamp(maze.floorpattern, adj, maze.floorcolor),
                    ptype=ptype_override, pnum=0,
                )

            elif obj == MazeObjIds.WALL_DESTRUCTABLE:
                adj = checkwalladj8(maze, x, y)
                stamp = wall_get_destructable_stamp(maze.wallpattern, adj, maze.wallcolor, maze.rand)

            elif obj == MazeObjIds.WALL_SECRET:
                adj = checkwalladj8(maze, x, y)
                stamp = dataclasses.replace(
                    wall_get_stamp(maze.wallpattern, adj, maze.wallcolor, maze.rand),
                    ptype="secret", pnum=0,
                )

            elif obj in _WALL_TILE_DOTS:
                dots = _WALL_TILE_DOTS[obj]
                adj = checkwalladj8(maze, x, y)
                stamp = wall_get_stamp(maze.wallpattern, adj, maze.wallcolor, maze.rand)

            elif obj == MazeObjIds.DOOR_HORIZ:
                adj = checkdooradj4(maze, x, y)
                stamp = door_get_stamp(DOOR_HORIZ, adj)
            elif obj == MazeObjIds.DOOR_VERT:
                adj = checkdooradj4(maze, x, y)
                stamp = door_get_stamp(DOOR_VERT, adj)

            elif obj == MazeObjIds.FOOD_INVULN:
                stamp = item_get_stamp(FOODS[maze.rand.intn(3)])

            elif obj == MazeObjIds.FORCEFIELDHUB:
                adj = checkffadj4(maze, x, y)
                stamp = ff_get_stamp(adj)

            elif obj in _ITEM_STAMP_NAMES:
                stamp = item_get_stamp(_ITEM_STAMP_NAMES[obj])

            if stamp is not None:
                write_stamp_to_image(img, stamp, x * 16 + 16 + stamp.nudgex, y * 16 + 16 + stamp.nudgey)

            if dots != 0:
                renderdots(img, x * 16 + 16, y * 16 + 16, dots)

    # Wrap arrows
    if maze.flags & LFLAG4_WRAP_H:
        left = item_get_stamp("arrowleft")
        right = item_get_stamp("arrowright")
        for i in range(2, 33):
            write_stamp_to_image(img, left, 0, i * 16)
            write_stamp_to_image(img, right, 32 * 16 + 16, i * 16)

    if maze.flags & LFLAG4_WRAP_V:
        up = item_get_stamp("arrowup")
        down = item_get_stamp("arrowdown")
        for i in range(1, 32):
            write_stamp_to_image(img, up, i * 16 + 16, 0)
            write_stamp_to_image(img, down, i * 16 + 16, 32 * 16 + 16)

    save_to_png(output, img)

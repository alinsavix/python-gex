"""Playfield rendering -- generates full maze images."""

from __future__ import annotations

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
    for i in range(1, 100):
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
                stamp.ptype = "forcefield"
                stamp.pnum = 0
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

            elif obj == MazeObjIds.TILE_STUN:
                adj = checkwalladj3(maze, x, y) + maze.rand.intn(4)
                stamp = floor_get_stamp(maze.floorpattern, adj, maze.floorcolor)
                stamp.ptype = "stun"
                stamp.pnum = 0

            elif obj == MazeObjIds.TILE_TRAP1:
                dots = 1
                adj = checkwalladj3(maze, x, y) + maze.rand.intn(4)
                stamp = floor_get_stamp(maze.floorpattern, adj, maze.floorcolor)
                stamp.ptype = "trap"
                stamp.pnum = 0
            elif obj == MazeObjIds.TILE_TRAP2:
                dots = 2
                adj = checkwalladj3(maze, x, y) + maze.rand.intn(4)
                stamp = floor_get_stamp(maze.floorpattern, adj, maze.floorcolor)
                stamp.ptype = "trap"
                stamp.pnum = 0
            elif obj == MazeObjIds.TILE_TRAP3:
                dots = 3
                adj = checkwalladj3(maze, x, y) + maze.rand.intn(4)
                stamp = floor_get_stamp(maze.floorpattern, adj, maze.floorcolor)
                stamp.ptype = "trap"
                stamp.pnum = 0

            elif obj == MazeObjIds.WALL_DESTRUCTABLE:
                adj = checkwalladj8(maze, x, y)
                stamp = wall_get_destructable_stamp(maze.wallpattern, adj, maze.wallcolor, maze.rand)
            elif obj == MazeObjIds.WALL_SECRET:
                adj = checkwalladj8(maze, x, y)
                stamp = wall_get_stamp(maze.wallpattern, adj, maze.wallcolor, maze.rand)
                stamp.ptype = "secret"
                stamp.pnum = 0

            elif obj == MazeObjIds.WALL_TRAPCYC1:
                dots = 1
                adj = checkwalladj8(maze, x, y)
                stamp = wall_get_stamp(maze.wallpattern, adj, maze.wallcolor, maze.rand)
            elif obj == MazeObjIds.WALL_TRAPCYC2:
                dots = 2
                adj = checkwalladj8(maze, x, y)
                stamp = wall_get_stamp(maze.wallpattern, adj, maze.wallcolor, maze.rand)
            elif obj == MazeObjIds.WALL_TRAPCYC3:
                dots = 3
                adj = checkwalladj8(maze, x, y)
                stamp = wall_get_stamp(maze.wallpattern, adj, maze.wallcolor, maze.rand)
            elif obj == MazeObjIds.WALL_RANDOM:
                dots = 4
                adj = checkwalladj8(maze, x, y)
                stamp = wall_get_stamp(maze.wallpattern, adj, maze.wallcolor, maze.rand)
            elif obj == MazeObjIds.WALL_REGULAR:
                adj = checkwalladj8(maze, x, y)
                stamp = wall_get_stamp(maze.wallpattern, adj, maze.wallcolor, maze.rand)

            elif obj == MazeObjIds.WALL_MOVABLE:
                stamp = item_get_stamp("pushwall")
            elif obj == MazeObjIds.KEY:
                stamp = item_get_stamp("key")

            elif obj == MazeObjIds.POWER_INVIS:
                stamp = item_get_stamp("invis")
            elif obj == MazeObjIds.POWER_REPULSE:
                stamp = item_get_stamp("repulse")
            elif obj == MazeObjIds.POWER_REFLECT:
                stamp = item_get_stamp("reflect")
            elif obj == MazeObjIds.POWER_TRANSPORT:
                stamp = item_get_stamp("transportability")
            elif obj == MazeObjIds.POWER_SUPERSHOT:
                stamp = item_get_stamp("supershot")
            elif obj == MazeObjIds.POWER_INVULN:
                stamp = item_get_stamp("invuln")

            elif obj == MazeObjIds.DOOR_HORIZ:
                adj = checkdooradj4(maze, x, y)
                stamp = door_get_stamp(DOOR_HORIZ, adj)
            elif obj == MazeObjIds.DOOR_VERT:
                adj = checkdooradj4(maze, x, y)
                stamp = door_get_stamp(DOOR_VERT, adj)

            elif obj == MazeObjIds.PLAYERSTART:
                stamp = item_get_stamp("plus")
            elif obj == MazeObjIds.EXIT:
                stamp = item_get_stamp("exit")
            elif obj == MazeObjIds.EXITTO6:
                stamp = item_get_stamp("exit6")

            elif obj == MazeObjIds.MONST_GHOST:
                stamp = item_get_stamp("ghost")
            elif obj == MazeObjIds.MONST_GRUNT:
                stamp = item_get_stamp("grunt")
            elif obj == MazeObjIds.MONST_DEMON:
                stamp = item_get_stamp("demon")
            elif obj == MazeObjIds.MONST_LOBBER:
                stamp = item_get_stamp("lobber")
            elif obj == MazeObjIds.MONST_SORC:
                stamp = item_get_stamp("sorcerer")
            elif obj == MazeObjIds.MONST_AUX_GRUNT:
                stamp = item_get_stamp("auxgrunt")
            elif obj == MazeObjIds.MONST_DEATH:
                stamp = item_get_stamp("death")
            elif obj == MazeObjIds.MONST_ACID:
                stamp = item_get_stamp("acid")
            elif obj == MazeObjIds.MONST_SUPERSORC:
                stamp = item_get_stamp("supersorc")
            elif obj == MazeObjIds.MONST_IT:
                stamp = item_get_stamp("it")
            elif obj == MazeObjIds.MONST_DRAGON:
                stamp = item_get_stamp("dragon")

            elif obj == MazeObjIds.GEN_GHOST1:
                stamp = item_get_stamp("ghostgen1")
            elif obj == MazeObjIds.GEN_GHOST2:
                stamp = item_get_stamp("ghostgen2")
            elif obj == MazeObjIds.GEN_GHOST3:
                stamp = item_get_stamp("ghostgen3")

            elif obj in (MazeObjIds.GEN_GRUNT1, MazeObjIds.GEN_DEMON1, MazeObjIds.GEN_LOBBER1,
                         MazeObjIds.GEN_SORC1, MazeObjIds.GEN_AUX_GRUNT1):
                stamp = item_get_stamp("generator1")
            elif obj in (MazeObjIds.GEN_GRUNT2, MazeObjIds.GEN_DEMON2, MazeObjIds.GEN_LOBBER2,
                         MazeObjIds.GEN_SORC2, MazeObjIds.GEN_AUX_GRUNT2):
                stamp = item_get_stamp("generator2")
            elif obj in (MazeObjIds.GEN_GRUNT3, MazeObjIds.GEN_DEMON3, MazeObjIds.GEN_LOBBER3,
                         MazeObjIds.GEN_SORC3, MazeObjIds.GEN_AUX_GRUNT3):
                stamp = item_get_stamp("generator3")

            elif obj == MazeObjIds.TREASURE:
                stamp = item_get_stamp("treasure")
            elif obj == MazeObjIds.TREASURE_LOCKED:
                stamp = item_get_stamp("treasurelocked")
            elif obj == MazeObjIds.TREASURE_BAG:
                stamp = item_get_stamp("goldbag")
            elif obj == MazeObjIds.FOOD_DESTRUCTABLE:
                stamp = item_get_stamp("food")
            elif obj == MazeObjIds.FOOD_INVULN:
                stamp = item_get_stamp(FOODS[maze.rand.intn(3)])
            elif obj == MazeObjIds.POT_DESTRUCTABLE:
                stamp = item_get_stamp("potion")
            elif obj == MazeObjIds.POT_INVULN:
                stamp = item_get_stamp("ipotion")

            elif obj == MazeObjIds.FORCEFIELDHUB:
                adj = checkffadj4(maze, x, y)
                stamp = ff_get_stamp(adj)
            elif obj == MazeObjIds.TRANSPORTER:
                stamp = item_get_stamp("tport")

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

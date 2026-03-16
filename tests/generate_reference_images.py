#!/usr/bin/env python3
"""Generate the reference image corpus for golden-file regression tests.

Run this script once (or whenever the rendering code intentionally changes)
to regenerate the reference images:

    uv run python tests/generate_reference_images.py

It produces PNG files and a manifest (SHA-256 hashes) under
tests/reference_images/.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

# Ensure the package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from PIL import Image

from gex.render import (
    blank_image,
    gen_image,
    gen_image_from_array,
    gen_stamp_from_array,
    save_to_png,
    write_stamp_to_image,
)
from gex.floor import floor_get_stamp
from gex.wall import wall_get_stamp, wall_get_destructable_stamp, ff_get_stamp
from gex.items import item_get_stamp
from gex.door import door_get_stamp, DOOR_HORIZ, DOOR_VERT
from gex.monsters import domonster
from gex.maze import domaze
from gex.roms import _rom_dir, TILE_ROMS

REF_DIR = Path(__file__).resolve().parent / "reference_images"


def _pixel_sha256(img: Image.Image) -> str:
    """SHA-256 of raw RGBA pixel data only, ignoring PNG metadata/encoding."""
    return hashlib.sha256(img.tobytes()).hexdigest()


def _stamp_to_image(stamp) -> Image:
    h = len(stamp.data) // stamp.width
    img = blank_image(stamp.width * 8, h * 8)
    write_stamp_to_image(img, stamp, 0, 0)
    return img


def main() -> None:
    rom_dir = _rom_dir()
    if not rom_dir.is_dir() or not (rom_dir / TILE_ROMS[0][0]).is_file():
        print(f"ERROR: ROM files not found at {rom_dir}", file=sys.stderr)
        sys.exit(1)

    REF_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}

    # --- Single tiles ---
    for tilenum in [0x11, 0x100, 0x1C1]:
        name = f"tile_{tilenum:#06x}"
        path = str(REF_DIR / f"{name}.png")
        img = gen_image(tilenum, 1, 1)
        save_to_png(path, img)
        manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": list(img.size)}

    # --- Tile grids ---
    for tilenum, xt, yt in [(0x100, 2, 2), (0x100, 4, 4)]:
        name = f"tilegrid_{tilenum:#06x}_{xt}x{yt}"
        path = str(REF_DIR / f"{name}.png")
        img = gen_image(tilenum, xt, yt)
        save_to_png(path, img)
        manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": list(img.size)}

    # --- Tile from array ---
    name = "tilearray_custom"
    path = str(REF_DIR / f"{name}.png")
    img = gen_image_from_array([0x100, 0x101, 0x102, 0x103], 2, 2)
    save_to_png(path, img)
    manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": list(img.size)}

    # --- Floors: sweep pattern x color combinations ---
    for pattern in [0, 3, 5, 8]:
        for color in [0, 5, 15]:
            for adj in [0, 4, 16, 28]:
                name = f"floor_p{pattern}_c{color}_a{adj}"
                path = str(REF_DIR / f"{name}.png")
                stamp = floor_get_stamp(pattern, adj, color)
                img = _stamp_to_image(stamp)
                save_to_png(path, img)
                manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": [16, 16]}

    # --- Walls: pattern x color x adjacency ---
    for pattern in [0, 2, 5]:
        for color in [0, 8]:
            for adj_val in [0x00, 0x0F, 0xFF]:
                name = f"wall_p{pattern}_c{color}_a{adj_val:#04x}"
                path = str(REF_DIR / f"{name}.png")
                stamp = wall_get_stamp(pattern, adj_val, color)
                img = _stamp_to_image(stamp)
                save_to_png(path, img)
                manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": [16, 16]}

    # --- Shrub walls ---
    for pattern in [6, 8, 11]:
        name = f"wall_shrub_p{pattern}"
        path = str(REF_DIR / f"{name}.png")
        stamp = wall_get_stamp(pattern, 0, 0)
        img = _stamp_to_image(stamp)
        save_to_png(path, img)
        manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": [16, 16]}

    # --- Destructible walls ---
    for pattern in [0, 3, 6]:
        name = f"wall_destruct_p{pattern}"
        path = str(REF_DIR / f"{name}.png")
        stamp = wall_get_destructable_stamp(pattern, 0, 0)
        img = _stamp_to_image(stamp)
        save_to_png(path, img)
        manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": [16, 16]}

    # --- Forcefields ---
    for adj in [0, 5, 10, 15]:
        name = f"ff_a{adj}"
        path = str(REF_DIR / f"{name}.png")
        stamp = ff_get_stamp(adj)
        img = _stamp_to_image(stamp)
        save_to_png(path, img)
        manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": [16, 16]}

    # --- Items ---
    for item_name in ["key", "food", "potion", "treasure", "dragon", "ghost",
                      "grunt", "demon", "exit", "tport", "blank", "invis",
                      "goldbag", "supershot", "invuln"]:
        name = f"item_{item_name}"
        path = str(REF_DIR / f"{name}.png")
        stamp = item_get_stamp(item_name)
        img = _stamp_to_image(stamp)
        save_to_png(path, img)
        manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": list(img.size)}

    # --- Doors ---
    for direction, dname in [(DOOR_HORIZ, "horiz"), (DOOR_VERT, "vert")]:
        for adj in [0, 3, 7, 15]:
            name = f"door_{dname}_a{adj}"
            path = str(REF_DIR / f"{name}.png")
            stamp = door_get_stamp(direction, adj)
            img = _stamp_to_image(stamp)
            save_to_png(path, img)
            manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": list(img.size)}

    # --- Monsters (ghost, various directions) ---
    for direction in ["up", "right", "down", "left", "upright", "downleft"]:
        name = f"ghost_walk_{direction}"
        path = str(REF_DIR / f"{name}.png")
        domonster(f"ghost-walk-{direction}", path, "base", 0, False)
        img = Image.open(path)
        manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": list(img.size)}

    # --- Ghost level variants ---
    for level in [1, 2, 3]:
        name = f"ghost{level}_walk_up"
        path = str(REF_DIR / f"{name}.png")
        domonster(f"ghost{level}-walk-up", path, "base", 0, False)
        img = Image.open(path)
        manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": list(img.size)}

    # --- Mazes (full render, small sample) ---
    for maze_num in [0, 10, 50, 100]:
        name = f"maze_{maze_num}"
        path = str(REF_DIR / f"{name}.png")
        domaze(f"maze{maze_num}", path, False)
        img = Image.open(path)
        manifest[name] = {"pixel_sha256": _pixel_sha256(img), "size": list(img.size)}

    # --- Write manifest ---
    manifest_path = REF_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    print(f"Generated {len(manifest)} reference images in {REF_DIR}")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()

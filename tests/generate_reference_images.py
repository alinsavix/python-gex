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
import csv
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
from gex.roms import (
    CODE_ROMS,
    SLAPSTIC_ROMS,
    TILE_ROMS,
    _rom_dir,
    slapstic_read_maze,
)

REF_DIR = Path(__file__).resolve().parent / "reference_images"
MAZE_CATALOG = Path(__file__).resolve().parent / "data" / "maze_catalog.csv"


def _pixel_sha256(img: Image.Image) -> str:
    """SHA-256 of raw RGBA pixel data only, ignoring PNG metadata/encoding."""
    return hashlib.sha256(img.tobytes()).hexdigest()


def _stamp_to_image(stamp) -> Image:
    h = len(stamp.data) // stamp.width
    img = blank_image(stamp.width * 8, h * 8)
    write_stamp_to_image(img, stamp, 0, 0)
    return img


def _required_rom_names() -> list[str]:
    groups = TILE_ROMS + CODE_ROMS + [SLAPSTIC_ROMS]
    return sorted({name for group in groups for name in group})


def _maze_catalog_metadata() -> dict[int, dict[str, int]]:
    """Validate all raw maze headers against the canonical generated catalog."""
    with MAZE_CATALOG.open(newline="") as stream:
        catalog = {int(row["maze"]): row for row in csv.DictReader(stream)}
    if set(catalog) != set(range(117)):
        raise RuntimeError(f"{MAZE_CATALOG} does not contain exactly mazes 0 through 116")

    result: dict[int, dict[str, int]] = {}
    for maze_num in range(117):
        row = catalog[maze_num]
        raw = slapstic_read_maze(maze_num)
        metadata = {
            "secret_trick": raw[0],
            "level_flags": int.from_bytes(raw[1:5], "big"),
            "playfield_patterns": raw[5],
            "playfield_colors": raw[6],
            "htype1": raw[7],
            "htype2": raw[8],
            "vtype1": raw[9],
            "vtype2": raw[10],
        }
        expected = {
            key: int(row[key], 16)
            for key in metadata
        }
        if metadata != expected:
            raise RuntimeError(
                f"maze {maze_num} header differs from {MAZE_CATALOG}: "
                f"ROM={metadata}, catalog={expected}"
            )
        expected_span = int(row["record_size"]) + int(
            row["bytes_after_record_to_boundary"]
        )
        if len(raw) != expected_span:
            raise RuntimeError(
                f"maze {maze_num} pointer span {len(raw)} != catalog span {expected_span}"
            )
        result[maze_num] = metadata
    return result


def main() -> None:
    rom_dir = _rom_dir()
    missing = [name for name in _required_rom_names() if not (rom_dir / name).is_file()]
    if missing:
        print(
            f"ERROR: {len(missing)} required ROM files not found at {rom_dir}: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        sys.exit(1)

    REF_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}
    maze_metadata = _maze_catalog_metadata()

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

    # --- Mazes (all 117 records, numbered 0 through 116) ---
    for maze_num in range(117):
        name = f"maze_{maze_num}"
        path = str(REF_DIR / f"{name}.png")
        domaze(f"maze{maze_num}", path, False)
        img = Image.open(path)
        manifest[name] = {
            "pixel_sha256": _pixel_sha256(img),
            "size": list(img.size),
            "maze_header": maze_metadata[maze_num],
        }

    # A successful complete render owns the maze_N.png namespace. Remove old
    # stale out-of-range artifacts.
    expected_maze_files = {f"maze_{maze_num}.png" for maze_num in range(117)}
    for path in REF_DIR.glob("maze_*.png"):
        if path.name not in expected_maze_files:
            path.unlink()

    # --- Write manifest ---
    manifest_path = REF_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    print(f"Generated {len(manifest)} reference images in {REF_DIR}")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()

"""ROM-independent structural checks for the checked-in golden maze corpus."""

import hashlib
import json
from pathlib import Path

from PIL import Image


REF_DIR = Path(__file__).resolve().parent / "reference_images"


def test_maze_manifest_and_files_are_exactly_0_through_116():
    manifest = json.loads((REF_DIR / "manifest.json").read_text())
    manifest_names = {name for name in manifest if name.startswith("maze_")}
    file_names = {path.stem for path in REF_DIR.glob("maze_*.png")}
    expected = {f"maze_{maze_num}" for maze_num in range(117)}
    assert manifest_names == expected
    assert file_names == expected


def test_every_reference_png_is_manifested_and_matches_its_pixel_hash():
    manifest = json.loads((REF_DIR / "manifest.json").read_text())
    expected_files = {f"{name}.png" for name in manifest}
    actual_files = {path.name for path in REF_DIR.glob("*.png")}
    assert actual_files == expected_files
    for name, entry in manifest.items():
        image = Image.open(REF_DIR / f"{name}.png")
        assert list(image.size) == entry["size"]
        assert hashlib.sha256(image.tobytes()).hexdigest() == entry["pixel_sha256"]

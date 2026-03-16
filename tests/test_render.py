"""Tests for the render module (pure logic, no ROM access)."""

import pytest
from unittest.mock import patch, MagicMock

from PIL import Image

from gex.render import (
    byte_to_bits,
    merge_planes,
    blank_image,
    irgb_to_rgba,
    write_tile_to_image,
    Stamp,
)
from gex.palettes import IRGB


class TestByteToBits:
    def test_all_zeros(self):
        # 0x00 = all bits clear -> all 1s (inverted logic: 0 means bit SET)
        assert byte_to_bits(0x00) == [1, 1, 1, 1, 1, 1, 1, 1]

    def test_all_ones(self):
        # 0xFF = all bits set -> all 0s
        assert byte_to_bits(0xFF) == [0, 0, 0, 0, 0, 0, 0, 0]

    def test_alternating(self):
        # 0xAA = 10101010 -> [0,1,0,1,0,1,0,1]
        assert byte_to_bits(0xAA) == [0, 1, 0, 1, 0, 1, 0, 1]

    def test_high_bit_only(self):
        # 0x80 = 10000000
        assert byte_to_bits(0x80) == [0, 1, 1, 1, 1, 1, 1, 1]

    def test_low_bit_only(self):
        # 0x01 = 00000001
        assert byte_to_bits(0x01) == [1, 1, 1, 1, 1, 1, 1, 0]

    def test_returns_8_elements(self):
        for b in range(256):
            assert len(byte_to_bits(b)) == 8


class TestMergePlanes:
    def test_all_zeros(self):
        planes = [[0] * 8 for _ in range(4)]
        assert merge_planes(planes) == [0] * 8

    def test_all_ones(self):
        planes = [[1] * 8 for _ in range(4)]
        assert merge_planes(planes) == [15] * 8

    def test_plane_weighting(self):
        # Only plane 0 set -> value 1
        planes = [[1] * 8, [0] * 8, [0] * 8, [0] * 8]
        assert merge_planes(planes) == [1] * 8

        # Only plane 1 set -> value 2
        planes = [[0] * 8, [1] * 8, [0] * 8, [0] * 8]
        assert merge_planes(planes) == [2] * 8

        # Only plane 2 set -> value 4
        planes = [[0] * 8, [0] * 8, [1] * 8, [0] * 8]
        assert merge_planes(planes) == [4] * 8

        # Only plane 3 set -> value 8
        planes = [[0] * 8, [0] * 8, [0] * 8, [1] * 8]
        assert merge_planes(planes) == [8] * 8

    def test_mixed_values(self):
        planes = [
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
        ]
        assert merge_planes(planes) == [1, 2, 4, 8, 0, 0, 0, 0]


class TestBlankImage:
    def test_creates_correct_size(self):
        img = blank_image(16, 32)
        assert img.size == (16, 32)

    def test_mode_is_rgba(self):
        img = blank_image(8, 8)
        assert img.mode == "RGBA"

    def test_all_transparent(self):
        img = blank_image(4, 4)
        pixels = img.load()
        for y in range(4):
            for x in range(4):
                assert pixels[x, y] == (0, 0, 0, 0)


class TestIrgbToRgba:
    def test_delegates_to_irgb(self):
        c = IRGB(0xFFFF)
        assert irgb_to_rgba(c) == c.to_rgba()


class TestWriteTileToImage:
    def _make_tile(self, val: int) -> list[list[int]]:
        return [[val] * 8 for _ in range(8)]

    def _make_palette(self) -> list[IRGB]:
        return [IRGB(i * 0x1111) for i in range(16)]

    def test_writes_tile_colors(self):
        img = blank_image(8, 8)
        tile = self._make_tile(5)
        palette = self._make_palette()
        write_tile_to_image(img, tile, palette, False, 0, 0)
        pixels = img.load()
        expected = palette[5].to_rgba()
        assert pixels[0, 0] == expected
        assert pixels[7, 7] == expected

    def test_trans0_skips_zero(self):
        img = blank_image(8, 8)
        tile = self._make_tile(0)
        palette = self._make_palette()
        write_tile_to_image(img, tile, palette, True, 0, 0)
        pixels = img.load()
        # Should remain transparent
        assert pixels[0, 0] == (0, 0, 0, 0)

    def test_trans0_false_writes_zero(self):
        img = blank_image(8, 8)
        tile = self._make_tile(0)
        palette = self._make_palette()
        write_tile_to_image(img, tile, palette, False, 0, 0)
        pixels = img.load()
        assert pixels[0, 0] == palette[0].to_rgba()

    def test_offset_positioning(self):
        img = blank_image(16, 16)
        tile = self._make_tile(3)
        palette = self._make_palette()
        write_tile_to_image(img, tile, palette, False, 8, 8)
        pixels = img.load()
        # Tile should be at offset (8,8)
        assert pixels[8, 8] == palette[3].to_rgba()
        # Original corner should be untouched
        assert pixels[0, 0] == (0, 0, 0, 0)

    def test_clips_to_image_bounds(self):
        img = blank_image(4, 4)
        tile = self._make_tile(1)
        palette = self._make_palette()
        # Should not raise even though tile extends beyond image
        write_tile_to_image(img, tile, palette, False, 0, 0)
        pixels = img.load()
        assert pixels[3, 3] == palette[1].to_rgba()

    def test_negative_offset_clips(self):
        img = blank_image(8, 8)
        tile = self._make_tile(2)
        palette = self._make_palette()
        # Negative offset should clip, not crash
        write_tile_to_image(img, tile, palette, False, -4, -4)
        pixels = img.load()
        assert pixels[0, 0] == palette[2].to_rgba()


class TestStamp:
    def test_defaults(self):
        s = Stamp(width=2, numbers=[1, 2, 3, 4], ptype="base", pnum=0)
        assert s.trans0 is False
        assert s.nudgex == 0
        assert s.nudgey == 0
        assert s.data == []

    def test_custom_fields(self):
        s = Stamp(width=3, numbers=[1, 2, 3], ptype="floor", pnum=5,
                  trans0=True, nudgex=-4, nudgey=-4)
        assert s.trans0 is True
        assert s.nudgex == -4

"""Tests for the palettes module."""

import pytest

from gex.palettes import (
    IRGB,
    FLOOR_PALETTES,
    WALL_PALETTES,
    BASE_PALETTES,
    GAUNTLET_PALETTES,
    TRAP_PALETTE,
    STUN_PALETTE,
    SECRET_PALETTE,
    FORCEFIELD_PALETTE,
    SHRUB_PALETTE,
    palette_clone,
    palette_make_special,
)


class TestIRGB:
    def test_black(self):
        c = IRGB(0x0000)
        assert c.to_rgba() == (0, 0, 0, 255)

    def test_white(self):
        c = IRGB(0xFFFF)
        r = 15 * 15
        assert c.to_rgba() == (r, r, r, 255)

    def test_pure_red(self):
        c = IRGB(0xFF00)
        assert c.to_rgba() == (15 * 15, 0, 0, 255)

    def test_pure_green(self):
        c = IRGB(0xF0F0)
        assert c.to_rgba() == (0, 15 * 15, 0, 255)

    def test_pure_blue(self):
        c = IRGB(0xF00F)
        assert c.to_rgba() == (0, 0, 15 * 15, 255)

    def test_mixed_color(self):
        # I=8, R=4, G=2, B=1 -> (32, 16, 8, 255)
        c = IRGB(0x8421)
        assert c.to_rgba() == (8 * 4, 8 * 2, 8 * 1, 255)

    def test_zero_intensity(self):
        c = IRGB(0x0FFF)
        assert c.to_rgba() == (0, 0, 0, 255)

    def test_repr(self):
        c = IRGB(0xABCD)
        assert repr(c) == "IRGB(0xABCD)"

    def test_repr_zero_padded(self):
        c = IRGB(0x0042)
        assert repr(c) == "IRGB(0x0042)"

    def test_alpha_always_255(self):
        for val in [0x0000, 0xFFFF, 0x8421, 0x1234]:
            assert IRGB(val).to_rgba()[3] == 255


class TestPaletteData:
    def test_floor_palettes_count(self):
        assert len(FLOOR_PALETTES) == 16

    def test_wall_palettes_count(self):
        assert len(WALL_PALETTES) == 17

    def test_base_palettes_count(self):
        assert len(BASE_PALETTES) == 12

    def test_palette_has_16_colors(self):
        for name, pals in GAUNTLET_PALETTES.items():
            for i, pal in enumerate(pals):
                assert len(pal) == 16, f"{name}[{i}] has {len(pal)} colors, expected 16"

    def test_gauntlet_palettes_keys(self):
        expected = {
            "teleff", "floor", "wall", "base", "warrior", "valkyrie",
            "wizard", "elf", "trap", "stun", "secret", "shrub", "forcefield",
        }
        assert set(GAUNTLET_PALETTES.keys()) == expected


class TestPaletteClone:
    def test_clone_copies_all_colors(self):
        src = [IRGB(i) for i in range(16)]
        dest = [IRGB(0) for _ in range(16)]
        palette_clone(dest, src)
        for i in range(16):
            assert dest[i].irgb == i

    def test_clone_overwrites_dest(self):
        src = [IRGB(0xFFFF) for _ in range(16)]
        dest = [IRGB(0x1234) for _ in range(16)]
        palette_clone(dest, src)
        assert all(c.irgb == 0xFFFF for c in dest)


class TestPaletteMakeSpecial:
    def test_trap_palette_gets_floor_colors(self):
        palette_make_special(0, 0, 0, 0)
        # Trap palette should be based on floor palette 0 with modified special colors
        assert TRAP_PALETTE[0][10].irgb == 0xA0AA  # S_COLORS_1[0] = 10
        assert TRAP_PALETTE[0][12].irgb == 0xA0AA  # S_COLORS_2[0] = 12

    def test_stun_palette_gets_floor_colors(self):
        palette_make_special(0, 0, 0, 0)
        assert STUN_PALETTE[0][10].irgb == 0xAAA0
        assert STUN_PALETTE[0][12].irgb == 0xAAA0

    def test_forcefield_palette_modified(self):
        palette_make_special(0, 0, 0, 0)
        assert FORCEFIELD_PALETTE[0][10].irgb == 0xAA00
        assert FORCEFIELD_PALETTE[0][12].irgb == 0xDA60

    def test_secret_palette_intensity_boosted(self):
        palette_make_special(0, 0, 0, 0)
        # Secret palette is derived from wall palette 0 with intensity +4
        for i in range(16):
            orig = WALL_PALETTES[0][i]
            orig_intensity = (orig.irgb & 0xF000) >> 12
            new_intensity = min(orig_intensity + 4, 0xF)
            expected = (orig.irgb & 0x0FFF) | (new_intensity << 12)
            assert SECRET_PALETTE[0][i].irgb == expected

    def test_shrub_palette_with_wallpattern_ge_6(self):
        palette_make_special(0, 0, 7, 2)
        # wallpattern >= 6 and wallcolor > 0 -> clones from WALL_PALETTES[wallcolor-1]
        assert SHRUB_PALETTE[0][0].irgb == WALL_PALETTES[1][0].irgb

"""Tests for ROM utility functions (pure logic, no file I/O)."""

import os
import pytest

from gex.roms import (
    GexError,
    _rom_dir,
    get_romset,
    Romset,
    coderom_get_by_addr,
    slapstic_maze_get_bank,
    CODE_ROM_START,
    SLAPSTIC_BANK_INFO,
)


class TestRomDir:
    def test_default_roms_dir(self, monkeypatch):
        monkeypatch.delenv("GEX_ROM_DIR", raising=False)
        assert str(_rom_dir()) == "ROMs"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("GEX_ROM_DIR", "/tmp/my_roms")
        assert str(_rom_dir()) == "/tmp/my_roms"


class TestGetRomset:
    def test_bank_0(self):
        actual_tile, roms = get_romset(0)
        assert actual_tile == 0x800  # bank 0 has offset 0x800
        assert len(roms) == 4

    def test_bank_boundaries(self):
        # Tile 0x800 is in bank 1
        actual_tile, roms = get_romset(0x800)
        assert actual_tile == 0  # bank 1 has offset 0

    def test_returns_four_rom_files(self):
        for tilenum in [0, 0x800, 0x1000, 0x1800, 0x2000]:
            _, roms = get_romset(tilenum)
            assert len(roms) == 4

    def test_tile_within_bank(self):
        # Tile 0x100 is in bank 0, offset = 0x100 + 0x800 = 0x900
        actual_tile, _ = get_romset(0x100)
        assert actual_tile == 0x100 + 0x800


class TestRomset:
    def test_creation(self):
        rs = Romset(0x800, ["a", "b", "c", "d"])
        assert rs.offset == 0x800
        assert rs.roms == ["a", "b", "c", "d"]


class TestCoderomGetByAddr:
    def test_first_bank(self):
        roms, offset = coderom_get_by_addr(CODE_ROM_START)
        assert len(roms) == 2
        assert offset == 0x8000  # first code ROM set has offset 0x8000

    def test_second_bank(self):
        roms, offset = coderom_get_by_addr(CODE_ROM_START + 0x8000)
        assert len(roms) == 2
        assert offset == 0  # second code ROM set has offset 0


class TestSlapsticMazeGetBank:
    def test_valid_maze_range(self):
        for i in range(117):
            bank = slapstic_maze_get_bank(i)
            assert 0 <= bank <= 3

    def test_first_mazes_bank_0(self):
        # First 32 mazes (8 entries * 4 mazes each) should be bank 0
        for i in range(32):
            assert slapstic_maze_get_bank(i) == 0

    def test_invalid_negative(self):
        with pytest.raises(GexError):
            slapstic_maze_get_bank(-1)

    def test_invalid_too_high(self):
        with pytest.raises(GexError):
            slapstic_maze_get_bank(117)


class TestGexError:
    def test_is_exception(self):
        with pytest.raises(GexError):
            raise GexError("test error")

    def test_message(self):
        try:
            raise GexError("something went wrong")
        except GexError as e:
            assert str(e) == "something went wrong"

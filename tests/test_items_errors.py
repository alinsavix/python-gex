"""Tests for item error paths and doitem dispatch."""

import pytest
from unittest.mock import patch, MagicMock

from gex.items import item_get_stamp, doitem, ITEM_STAMPS
from gex.roms import GexError


class TestItemGetStampErrors:
    def test_unknown_item_raises_gexerror(self):
        with pytest.raises(GexError, match="requested bad item: nonexistent"):
            item_get_stamp("nonexistent")

    def test_empty_string_raises_gexerror(self):
        with pytest.raises(GexError, match="requested bad item: "):
            item_get_stamp("")

    def test_wrong_case_raises_gexerror(self):
        with pytest.raises(GexError, match="requested bad item: Key"):
            item_get_stamp("Key")

    def test_partial_name_raises_gexerror(self):
        with pytest.raises(GexError, match="requested bad item: ke"):
            item_get_stamp("ke")

    def test_error_message_includes_item_name(self):
        bad_name = "totally_bogus_item"
        with pytest.raises(GexError) as exc_info:
            item_get_stamp(bad_name)
        assert bad_name in str(exc_info.value)


class TestDoitem:
    def test_doitem_unknown_type_raises_gexerror(self):
        """doitem with an unrecognised token results in empty item_type -> GexError."""
        with pytest.raises(GexError):
            doitem("item-unknowntype", "out.png")

    def test_doitem_key_calls_save(self):
        mock_stamp = MagicMock()
        mock_stamp.width = 2
        mock_stamp.numbers = [0] * 4

        with patch("gex.items.item_get_stamp", return_value=mock_stamp) as mock_get:
            with patch("gex.items.render_stamp_to_file") as mock_render:
                doitem("item-key", "out.png")

        mock_get.assert_called_once_with("key")
        mock_render.assert_called_once_with(mock_stamp, "out.png")

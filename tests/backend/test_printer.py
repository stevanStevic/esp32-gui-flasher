"""Tests for esp_flasher.backend.printer module (printer factory)."""
import sys
from unittest.mock import patch, MagicMock

import pytest


class TestGetPrinter:
    """Tests for get_printer factory function."""

    @patch("esp_flasher.backend.printer.platform.system", return_value="Linux")
    @patch("esp_flasher.backend.printer.BrotherQLPrinter")
    def test_linux_returns_brother_printer(self, mock_brother_cls, mock_system):
        """On Linux, returns a BrotherQLPrinter instance."""
        from esp_flasher.backend.printer import get_printer

        result = get_printer("Brother_QL-600")

        mock_brother_cls.assert_called_once_with("Brother_QL-600")
        assert result == mock_brother_cls.return_value

    @patch("esp_flasher.backend.printer.platform.system", return_value="Windows")
    def test_windows_returns_windows_printer(self, mock_system):
        """On Windows, lazy-imports and returns a WindowsPrinter instance."""
        # Create fake win32 modules so the lazy import inside get_printer succeeds
        mock_win32ui = MagicMock()
        mock_win32con = MagicMock()

        # Temporarily inject fake modules and remove any cached win_printer module
        with patch.dict(sys.modules, {
            "win32ui": mock_win32ui,
            "win32con": mock_win32con,
        }):
            # Remove cached module so it re-imports with our fakes
            sys.modules.pop("esp_flasher.backend.printers.win_printer", None)

            from esp_flasher.backend.printer import get_printer
            result = get_printer("HP LaserJet")

            # Should be a WindowsPrinter instance
            from esp_flasher.backend.printers.win_printer import WindowsPrinter
            assert isinstance(result, WindowsPrinter)
            assert result.printer_name == "HP LaserJet"

    @patch("esp_flasher.backend.printer.platform.system", return_value="Darwin")
    def test_unsupported_os_raises(self, mock_system):
        """Unsupported OS raises ValueError."""
        from esp_flasher.backend.printer import get_printer

        with pytest.raises(ValueError, match="Unsupported OS for printing"):
            get_printer("SomePrinter")

    @patch("esp_flasher.backend.printer.platform.system", return_value="Linux")
    @patch("esp_flasher.backend.printer.BrotherQLPrinter")
    def test_printer_name_passed_through(self, mock_brother_cls, mock_system):
        """Printer name is correctly passed to the constructor."""
        from esp_flasher.backend.printer import get_printer

        get_printer("usb://0x04f9:0x20a7")
        mock_brother_cls.assert_called_once_with("usb://0x04f9:0x20a7")

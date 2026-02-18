"""Tests for esp_flasher.helpers.printer_utils module."""
from unittest.mock import patch, MagicMock

import pytest

from esp_flasher.helpers.printer_utils import list_available_printers


class TestListAvailablePrinters:
    """Tests for list_available_printers function."""

    @patch("esp_flasher.helpers.printer_utils.platform.system", return_value="Linux")
    @patch("subprocess.run")
    def test_linux_printers(self, mock_run, mock_system):
        """On Linux, parses lpstat output for printer names."""
        mock_run.return_value = MagicMock(
            stdout="printer Brother_QL-600 is idle.\nprinter HP_LaserJet is idle.\n"
        )

        from esp_flasher.helpers.printer_utils import list_available_printers
        result = list_available_printers()

        assert "Brother_QL-600" in result
        assert "HP_LaserJet" in result
        assert len(result) == 2

    @patch("esp_flasher.helpers.printer_utils.platform.system", return_value="Linux")
    @patch("subprocess.run", side_effect=Exception("lpstat not found"))
    def test_linux_subprocess_error(self, mock_run, mock_system):
        """Subprocess error returns empty list."""
        from esp_flasher.helpers.printer_utils import list_available_printers
        result = list_available_printers()
        assert result == []

    @patch("esp_flasher.helpers.printer_utils.platform.system", return_value="Darwin")
    def test_unsupported_os(self, mock_system):
        """Unsupported OS returns empty list."""
        from esp_flasher.helpers.printer_utils import list_available_printers
        result = list_available_printers()
        assert result == []

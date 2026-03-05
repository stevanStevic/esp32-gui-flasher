"""Tests for esp_flasher.helpers.serial_utils module."""
from unittest.mock import patch, MagicMock

import pytest

from esp_flasher.helpers.serial_utils import list_serial_ports


class TestListSerialPorts:
    """Tests for list_serial_ports function."""

    @patch("esp_flasher.helpers.serial_utils.esptool")
    def test_returns_port_list(self, mock_esptool):
        """Should delegate to esptool.get_port_list."""
        mock_esptool.get_port_list.return_value = [
            ("/dev/ttyUSB0", "USB Serial"),
            ("/dev/ttyUSB1", "CP2102"),
        ]
        result = list_serial_ports()
        assert len(result) == 2
        assert result[0] == ("/dev/ttyUSB0", "USB Serial")

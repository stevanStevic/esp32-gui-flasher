"""Tests for esp_flasher.helpers.serial_utils module."""
from unittest.mock import patch, MagicMock

import pytest

from esp_flasher.helpers.serial_utils import list_serial_ports, select_port
from esp_flasher.helpers.utils import Esp_flasherError


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


class TestSelectPort:
    """Tests for select_port function."""

    def test_explicit_port(self):
        """When args.port is set, returns it directly."""
        args = MagicMock()
        args.port = "/dev/ttyUSB0"

        result = select_port(args)
        assert result == "/dev/ttyUSB0"

    @patch("esp_flasher.helpers.serial_utils.list_serial_ports")
    def test_auto_detect_single(self, mock_list):
        """Single port detected: auto-selects it."""
        mock_list.return_value = [("/dev/ttyUSB0", "USB Serial")]
        args = MagicMock()
        args.port = None

        result = select_port(args)
        assert result == "/dev/ttyUSB0"

    @patch("esp_flasher.helpers.serial_utils.list_serial_ports")
    def test_no_ports_raises(self, mock_list):
        """No ports found: raises Esp_flasherError."""
        mock_list.return_value = []
        args = MagicMock()
        args.port = None

        with pytest.raises(Esp_flasherError, match="No serial port found"):
            select_port(args)

    @patch("esp_flasher.helpers.serial_utils.list_serial_ports")
    def test_multiple_ports_raises(self, mock_list):
        """Multiple ports found without --port: raises Esp_flasherError."""
        mock_list.return_value = [
            ("/dev/ttyUSB0", "USB Serial"),
            ("/dev/ttyUSB1", "CP2102"),
        ]
        args = MagicMock()
        args.port = None

        with pytest.raises(Esp_flasherError):
            select_port(args)

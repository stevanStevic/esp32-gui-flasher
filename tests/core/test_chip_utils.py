"""Tests for esp_flasher.core.chip module."""
from unittest.mock import patch, MagicMock

import pytest

from esp_flasher.core.chip import (
    EsptoolFlashArgs,
    ChipInfo,
    ESP32ChipInfo,
    read_chip_info,
    read_chip_property,
    chip_run_stub,
    detect_chip,
    get_chip_info,
)
from esp_flasher.core.errors import EspFlasherError


class TestEsptoolFlashArgs:
    """Tests for EsptoolFlashArgs data class."""

    def test_construction(self):
        args = EsptoolFlashArgs(
            chip="esp32s3",
            write_flash_args=["--flash_mode", "dio"],
            flash_size="8MB",
            addr_filename=["0x0", "boot.bin"],
            flash_mode="dio",
            flash_freq="80m",
            stub=True,
            before="default_reset",
            after="hard_reset",
        )
        assert args.chip == "esp32s3"
        assert args.flash_size == "8MB"
        assert args.no_stub is False  # stub=True → no_stub=False
        assert args.before == "default_reset"
        assert args.after == "hard_reset"

    def test_no_stub_inversion(self):
        """stub=False should result in no_stub=True."""
        args = EsptoolFlashArgs(
            chip="esp32",
            write_flash_args=[],
            flash_size="4MB",
            addr_filename=[],
            flash_mode="qio",
            flash_freq="40m",
            stub=False,
            before="default_reset",
            after="hard_reset",
        )
        assert args.no_stub is True


class TestChipInfoClasses:
    """Tests for ChipInfo, ESP32ChipInfo, ESP8266ChipInfo data classes."""

    def test_chip_info_as_dict(self):
        info = ChipInfo(family="ESP32", model="ESP32-D0WDQ6", mac="AA:BB:CC:DD:EE:FF")
        d = info.as_dict()
        assert d["family"] == "ESP32"
        assert d["model"] == "ESP32-D0WDQ6"
        assert d["mac"] == "AA:BB:CC:DD:EE:FF"

    def test_esp32_chip_info_as_dict(self):
        info = ESP32ChipInfo(
            model="ESP32-D0WDQ6 (revision 1)",
            mac="AA:BB:CC:DD:EE:FF",
            num_cores=2,
            cpu_frequency="240MHz",
            has_bluetooth=True,
            has_embedded_flash=False,
            has_factory_calibrated_adc=True,
        )
        d = info.as_dict()
        assert d["family"] == "ESP32"
        assert d["num_cores"] == 2
        assert d["cpu_frequency"] == "240MHz"
        assert d["has_bluetooth"] is True
        assert d["has_embedded_flash"] is False
        assert d["has_factory_calibrated_adc"] is True


class TestReadChipInfo:
    """Tests for read_chip_info function."""

    @patch("esp_flasher.core.chip.read_chip_property")
    def test_esp32_chip_info(self, mock_read_prop):
        """Should return ESP32ChipInfo with correctly parsed features."""
        import esptool

        # Create a mock that passes isinstance check
        mock_chip = MagicMock(spec=esptool.ESP32ROM)

        # read_chip_property is called for: read_mac, get_chip_description, get_chip_features
        mock_read_prop.side_effect = [
            [0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF],  # read_mac
            "ESP32-D0WDQ6 (revision 1)",               # get_chip_description
            "240MHz, Dual Core, WiFi, BT, Embedded Flash",  # get_chip_features
        ]

        result = read_chip_info(mock_chip)

        assert isinstance(result, ESP32ChipInfo)
        assert result.mac == "AA:BB:CC:DD:EE:FF"
        assert result.model == "ESP32-D0WDQ6 (revision 1)"
        assert result.num_cores == 2
        assert result.cpu_frequency == "240MHz"
        assert result.has_bluetooth is True
        assert result.has_embedded_flash is True

    @patch("esp_flasher.core.chip.read_chip_property")
    def test_esp32_single_core(self, mock_read_prop):
        """Single core chip should have num_cores=1."""
        import esptool

        mock_chip = MagicMock(spec=esptool.ESP32ROM)
        mock_read_prop.side_effect = [
            [0x11, 0x22, 0x33, 0x44, 0x55, 0x66],
            "ESP32-S0WDQ6",
            "160MHz, Single Core, WiFi",
        ]

        result = read_chip_info(mock_chip)
        assert result.num_cores == 1
        assert result.cpu_frequency == "160MHz"
        assert result.has_bluetooth is False

    @patch("esp_flasher.core.chip.read_chip_property")
    def test_unknown_chip_raises(self, mock_read_prop):
        """Non-ESP32 chip should raise EspFlasherError."""
        mock_chip = MagicMock()  # Not an ESP32ROM instance
        mock_read_prop.return_value = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66]

        with pytest.raises(EspFlasherError, match="Unknown chip type"):
            read_chip_info(mock_chip)


class TestReadChipProperty:
    """Tests for read_chip_property function."""

    @patch("esp_flasher.core.chip.prevent_print")
    def test_success(self, mock_prevent):
        """Should delegate to prevent_print and return result."""
        mock_prevent.return_value = "test_value"
        mock_func = MagicMock()

        result = read_chip_property(mock_func, "arg1", key="val")
        mock_prevent.assert_called_once_with(mock_func, "arg1", key="val")
        assert result == "test_value"

    @patch("esp_flasher.core.chip.prevent_print")
    def test_fatal_error(self, mock_prevent):
        """esptool.FatalError should be wrapped in EspFlasherError."""
        import esptool
        mock_prevent.side_effect = esptool.FatalError("chip read error")

        with pytest.raises(EspFlasherError, match="Reading chip details failed"):
            read_chip_property(MagicMock())


class TestDetectChip:
    """Tests for detect_chip function."""

    @patch("esp_flasher.core.chip.esptool")
    def test_success(self, mock_esptool):
        """Should return the connected device."""
        mock_chip = MagicMock()
        mock_esptool.get_default_connected_device.return_value = mock_chip

        result = detect_chip("/dev/ttyUSB0", baud=115200)

        assert result == mock_chip
        mock_esptool.get_default_connected_device.assert_called_once_with(
            serial_list=["/dev/ttyUSB0"],
            port="/dev/ttyUSB0",
            connect_attempts=1,
            initial_baud=115200,
        )

    @patch("esp_flasher.core.chip.esptool")
    def test_fatal_error(self, mock_esptool):
        """FatalError should be wrapped in EspFlasherError."""
        mock_esptool.FatalError = type("FatalError", (Exception,), {})
        mock_esptool.get_default_connected_device.side_effect = mock_esptool.FatalError("no device")

        with pytest.raises(EspFlasherError, match="ESP Chip Auto-Detection failed"):
            detect_chip("/dev/ttyUSB0")


class TestChipRunStub:
    """Tests for chip_run_stub function."""

    def test_success(self):
        mock_chip = MagicMock()
        mock_chip.run_stub.return_value = "stub_result"

        result = chip_run_stub(mock_chip)
        assert result == "stub_result"

    def test_fatal_error(self):
        import esptool
        mock_chip = MagicMock()
        mock_chip.run_stub.side_effect = esptool.FatalError("stub failed")

        with pytest.raises(EspFlasherError, match="Error putting ESP in stub flash mode"):
            chip_run_stub(mock_chip)


class TestGetChipInfo:
    """Tests for get_chip_info convenience function."""

    @patch("esp_flasher.core.chip.read_chip_info")
    @patch("esp_flasher.core.chip.detect_chip")
    def test_returns_info_and_closes_port(self, mock_detect, mock_read):
        mock_chip = MagicMock()
        mock_detect.return_value = mock_chip
        mock_info = MagicMock()
        mock_read.return_value = mock_info

        result = get_chip_info("/dev/ttyUSB0")

        assert result is mock_info
        mock_detect.assert_called_once_with("/dev/ttyUSB0")
        mock_read.assert_called_once_with(mock_chip)
        mock_chip._port.close.assert_called_once()

    @patch("esp_flasher.core.chip.read_chip_info")
    @patch("esp_flasher.core.chip.detect_chip")
    def test_closes_port_on_error(self, mock_detect, mock_read):
        mock_chip = MagicMock()
        mock_detect.return_value = mock_chip
        mock_read.side_effect = RuntimeError("read failed")

        with pytest.raises(RuntimeError, match="read failed"):
            get_chip_info("/dev/ttyUSB0")

        mock_chip._port.close.assert_called_once()


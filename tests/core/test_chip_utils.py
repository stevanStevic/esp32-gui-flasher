"""Tests for esp_flasher.core.chip_utils module."""
import io
import struct
from unittest.mock import patch, MagicMock

import pytest

from esp_flasher.core.chip_utils import (
    EsptoolFlashArgs,
    ChipInfo,
    ESP32ChipInfo,
    ESP8266ChipInfo,
    read_chip_info,
    read_chip_property,
    chip_run_stub,
    detect_flash_size,
    read_firmware_info,
    format_bootloader_path,
    detect_chip,
)
from esp_flasher.helpers.utils import Esp_flasherError


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
        assert args.encrypt is False
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
        assert d["is_esp32"] is None

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

    def test_esp8266_chip_info_as_dict(self):
        info = ESP8266ChipInfo(
            model="ESP8266EX",
            mac="11:22:33:44:55:66",
            chip_id=12345,
        )
        d = info.as_dict()
        assert d["family"] == "ESP8266"
        assert d["chip_id"] == 12345


class TestReadChipInfo:
    """Tests for read_chip_info function."""

    @patch("esp_flasher.core.chip_utils.read_chip_property")
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

    @patch("esp_flasher.core.chip_utils.read_chip_property")
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

    @patch("esp_flasher.core.chip_utils.read_chip_property")
    def test_unknown_chip_raises(self, mock_read_prop):
        """Non-ESP32 chip should raise Esp_flasherError."""
        mock_chip = MagicMock()  # Not an ESP32ROM instance
        mock_read_prop.return_value = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66]

        with pytest.raises(Esp_flasherError, match="Unknown chip type"):
            read_chip_info(mock_chip)


class TestReadChipProperty:
    """Tests for read_chip_property function."""

    @patch("esp_flasher.core.chip_utils.prevent_print")
    def test_success(self, mock_prevent):
        """Should delegate to prevent_print and return result."""
        mock_prevent.return_value = "test_value"
        mock_func = MagicMock()

        result = read_chip_property(mock_func, "arg1", key="val")
        mock_prevent.assert_called_once_with(mock_func, "arg1", key="val")
        assert result == "test_value"

    @patch("esp_flasher.core.chip_utils.prevent_print")
    def test_fatal_error(self, mock_prevent):
        """esptool.FatalError should be wrapped in Esp_flasherError."""
        import esptool
        mock_prevent.side_effect = esptool.FatalError("chip read error")

        with pytest.raises(Esp_flasherError, match="Reading chip details failed"):
            read_chip_property(MagicMock())


class TestDetectChip:
    """Tests for detect_chip function."""

    @patch("esp_flasher.core.chip_utils.esptool")
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

    @patch("esp_flasher.core.chip_utils.esptool")
    def test_fatal_error(self, mock_esptool):
        """FatalError should be wrapped in Esp_flasherError."""
        mock_esptool.FatalError = type("FatalError", (Exception,), {})
        mock_esptool.get_default_connected_device.side_effect = mock_esptool.FatalError("no device")

        with pytest.raises(Esp_flasherError, match="ESP Chip Auto-Detection failed"):
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

        with pytest.raises(Esp_flasherError, match="Error putting ESP in stub flash mode"):
            chip_run_stub(mock_chip)


class TestDetectFlashSize:
    """Tests for detect_flash_size function."""

    @patch("esp_flasher.core.chip_utils.read_chip_property")
    @patch("esp_flasher.core.chip_utils.esptool")
    def test_known_size(self, mock_esptool, mock_read_prop):
        """Known flash ID returns correct size from DETECTED_FLASH_SIZES."""
        mock_esptool.DETECTED_FLASH_SIZES = {0x40: "8MB", 0x20: "4MB"}
        mock_read_prop.return_value = 0x00400000  # flash_id >> 16 = 0x40

        mock_stub = MagicMock()
        result = detect_flash_size(mock_stub)
        assert result == "8MB"

    @patch("esp_flasher.core.chip_utils.read_chip_property")
    @patch("esp_flasher.core.chip_utils.esptool")
    def test_unknown_size_defaults_4mb(self, mock_esptool, mock_read_prop):
        """Unknown flash ID should default to 4MB."""
        mock_esptool.DETECTED_FLASH_SIZES = {}
        mock_read_prop.return_value = 0x00FF0000

        result = detect_flash_size(MagicMock())
        assert result == "4MB"


class TestReadFirmwareInfo:
    """Tests for read_firmware_info function."""

    @patch("esp_flasher.core.chip_utils.esptool")
    def test_valid_firmware(self, mock_esptool):
        """Valid firmware header returns (flash_mode, flash_freq)."""
        mock_esptool.ESPLoader.ESP_IMAGE_MAGIC = 0xE9

        # Header: magic=0xE9, segment_count=0x01, flash_mode=2 (dio), flash_size_freq=0x0F (80m)
        header = struct.pack("BBBB", 0xE9, 0x01, 0x02, 0x0F)
        firmware = io.BytesIO(header)

        mode, freq = read_firmware_info(firmware)
        assert mode == "dio"
        assert freq == "80m"
        # Verify seek(0) was called — file position should be at start
        assert firmware.tell() == 0

    @patch("esp_flasher.core.chip_utils.esptool")
    def test_invalid_magic(self, mock_esptool):
        """Invalid magic byte raises Esp_flasherError."""
        mock_esptool.ESPLoader.ESP_IMAGE_MAGIC = 0xE9

        header = struct.pack("BBBB", 0xFF, 0x00, 0x00, 0x00)
        firmware = io.BytesIO(header)

        with pytest.raises(Esp_flasherError, match="firmware binary is invalid"):
            read_firmware_info(firmware)

    @patch("esp_flasher.core.chip_utils.esptool")
    def test_qio_40m(self, mock_esptool):
        """flash_mode=0 (qio), flash_freq=0 (40m)."""
        mock_esptool.ESPLoader.ESP_IMAGE_MAGIC = 0xE9

        header = struct.pack("BBBB", 0xE9, 0x01, 0x00, 0x00)
        firmware = io.BytesIO(header)

        mode, freq = read_firmware_info(firmware)
        assert mode == "qio"
        assert freq == "40m"


class TestFormatBootloaderPath:
    """Tests for format_bootloader_path function."""

    def test_replacement(self):
        result = format_bootloader_path(
            "bootloader_$FLASH_MODE$_$FLASH_FREQ$.bin", "dio", "80m"
        )
        assert result == "bootloader_dio_80m.bin"

    def test_no_placeholders(self):
        result = format_bootloader_path("bootloader.bin", "dio", "80m")
        assert result == "bootloader.bin"

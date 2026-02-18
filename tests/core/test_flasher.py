"""Tests for esp_flasher.core.flasher module."""
from unittest.mock import patch, MagicMock, call

import pytest

from esp_flasher.core.chip_utils import EsptoolFlashArgs
from esp_flasher.helpers.utils import Esp_flasherError


def _make_firmware_args(chip="esp32s3", no_stub=False):
    """Helper to create a mock EsptoolFlashArgs."""
    return EsptoolFlashArgs(
        chip=chip,
        write_flash_args=["--flash_mode", "dio", "--flash_freq", "80m", "--flash_size", "8MB"],
        flash_size="8MB",
        addr_filename=["0x0", "/tmp/bootloader.bin", "0x10000", "/tmp/app.bin"],
        flash_mode="dio",
        flash_freq="80m",
        stub=not no_stub,  # EsptoolFlashArgs inverts this: no_stub = not stub
        before="default_reset",
        after="hard_reset",
    )


@patch("esp_flasher.core.flasher.esptool")
@patch("esp_flasher.core.flasher.configure_write_flash_args")
@patch("esp_flasher.core.flasher.extract_firmware")
@patch("esp_flasher.core.flasher.load_config")
class TestRunEspFlasher:
    """Tests for run_esp_flasher function."""

    def test_flash_basic(self, mock_config, mock_extract, mock_configure, mock_esptool):
        """Basic flash with no security features: verify esptool.main receives correct args."""
        mock_config.return_value = {"flash_encryption": {}, "secure_boot": {}}
        mock_extract.return_value = ({"security": {}}, "/tmp/extract")
        mock_configure.return_value = _make_firmware_args()

        from esp_flasher.core.flasher import run_esp_flasher
        run_esp_flasher("/dev/ttyUSB0", "/path/firmware.zip", baud_rate=460800)

        mock_esptool.main.assert_called_once()
        args = mock_esptool.main.call_args[0][0]

        assert "--chip" in args
        assert "esp32s3" in args
        assert "--port" in args
        assert "/dev/ttyUSB0" in args
        assert "--baud" in args
        assert "460800" in args
        assert "--before" in args
        assert "default_reset" in args
        assert "--after" in args
        assert "hard_reset" in args
        assert "write_flash" in args
        assert "0x0" in args
        assert "/tmp/bootloader.bin" in args

    def test_flash_no_stub(self, mock_config, mock_extract, mock_configure, mock_esptool):
        """When stub=False, --no-stub should appear in esptool command."""
        mock_config.return_value = {"flash_encryption": {}, "secure_boot": {}}
        mock_extract.return_value = ({"security": {}}, "/tmp/extract")
        mock_configure.return_value = _make_firmware_args(no_stub=True)

        from esp_flasher.core.flasher import run_esp_flasher
        run_esp_flasher("/dev/ttyUSB0", "/path/firmware.zip")

        args = mock_esptool.main.call_args[0][0]
        assert "--no-stub" in args

    @patch("esp_flasher.core.flasher.enable_flash_encryption")
    def test_flash_with_app_encryption(
        self, mock_encrypt, mock_config, mock_extract, mock_configure, mock_esptool
    ):
        """When app config enables encryption, enable_flash_encryption should be called."""
        mock_config.return_value = {
            "flash_encryption": {"encryption_en": True, "encryption_key_block_index": 1},
            "secure_boot": {},
        }
        mock_extract.return_value = ({"security": {}}, "/tmp/extract")
        mock_configure.return_value = _make_firmware_args()

        from esp_flasher.core.flasher import run_esp_flasher
        run_esp_flasher("/dev/ttyUSB0", "/path/firmware.zip")

        mock_encrypt.assert_called_once_with(
            {"encryption_en": True, "encryption_key_block_index": 1},
            "/dev/ttyUSB0",
            "/tmp/extract",
        )

    @patch("esp_flasher.core.flasher.enable_secure_boot")
    def test_flash_with_secure_boot(
        self, mock_secure_boot, mock_config, mock_extract, mock_configure, mock_esptool
    ):
        """When flasher_args enables secure boot, enable_secure_boot should be called."""
        mock_config.return_value = {
            "flash_encryption": {},
            "secure_boot": {"public_key_digest_block_index": 0},
        }
        flasher_args = {"security": {"secure_boot": True, "digest_file": "digest.bin"}}
        mock_extract.return_value = (flasher_args, "/tmp/extract")
        mock_configure.return_value = _make_firmware_args()

        from esp_flasher.core.flasher import run_esp_flasher
        run_esp_flasher("/dev/ttyUSB0", "/path/firmware.zip", baud_rate=115200)

        mock_secure_boot.assert_called_once_with(
            {"public_key_digest_block_index": 0},
            "/dev/ttyUSB0",
            115200,
            flasher_args,
            "/tmp/extract",
        )

    @patch("esp_flasher.core.flasher.burn_and_protect_security_efuses")
    @patch("esp_flasher.core.flasher.enable_secure_boot")
    @patch("esp_flasher.core.flasher.enable_flash_encryption")
    def test_flash_with_both_security_burns_efuses(
        self, mock_encrypt, mock_secure_boot, mock_burn_efuses,
        mock_config, mock_extract, mock_configure, mock_esptool
    ):
        """When both encryption and secure boot enabled, burn_and_protect should be called after flash."""
        mock_config.return_value = {
            "flash_encryption": {"encryption_en": True},
            "secure_boot": {"public_key_digest_block_index": 0},
        }
        flasher_args = {"security": {"secure_boot": True, "encryption": True}}
        mock_extract.return_value = (flasher_args, "/tmp/extract")
        mock_configure.return_value = _make_firmware_args()

        from esp_flasher.core.flasher import run_esp_flasher
        run_esp_flasher("/dev/ttyUSB0", "/path/firmware.zip")

        mock_esptool.main.assert_called_once()
        mock_burn_efuses.assert_called_once_with("/dev/ttyUSB0")

    def test_flash_esptool_fatal_error(
        self, mock_config, mock_extract, mock_configure, mock_esptool
    ):
        """When esptool raises FatalError, should raise Esp_flasherError."""
        mock_config.return_value = {"flash_encryption": {}, "secure_boot": {}}
        mock_extract.return_value = ({"security": {}}, "/tmp/extract")
        mock_configure.return_value = _make_firmware_args()
        mock_esptool.FatalError = type("FatalError", (Exception,), {})
        mock_esptool.main.side_effect = mock_esptool.FatalError("write failed")

        from esp_flasher.core.flasher import run_esp_flasher
        with pytest.raises(Esp_flasherError, match="Error while writing flash"):
            run_esp_flasher("/dev/ttyUSB0", "/path/firmware.zip")

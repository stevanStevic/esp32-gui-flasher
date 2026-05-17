"""Tests for esp_flasher.core.firmware module."""
import json
import os
import zipfile
from unittest.mock import patch, MagicMock, call

import pytest

from esp_flasher.core.errors import EspFlasherError


class TestExtractFirmware:
    """Tests for extract_firmware function."""

    def test_extract_success(self, firmware_zip, sample_flasher_args):
        """Successful extraction returns (flasher_args dict, temp_dir path)."""
        from esp_flasher.core.firmware import extract_firmware

        flasher_args, temp_dir = extract_firmware(firmware_zip)

        assert isinstance(flasher_args, dict)
        assert flasher_args["extra_esptool_args"]["chip"] == "esp32s3"
        assert os.path.isdir(temp_dir)
        assert os.path.exists(os.path.join(temp_dir, "flasher_args.json"))
        assert os.path.exists(os.path.join(temp_dir, "bootloader.bin"))
        assert os.path.exists(os.path.join(temp_dir, "app.bin"))

    def test_extract_file_not_found(self):
        """Non-existent firmware path raises FileNotFoundError."""
        from esp_flasher.core.firmware import extract_firmware

        with pytest.raises(FileNotFoundError, match="Firmware file not found"):
            extract_firmware("/nonexistent/firmware.zip")

    def test_extract_missing_flasher_args(self, tmp_path):
        """ZIP without flasher_args.json raises FileNotFoundError."""
        from esp_flasher.core.firmware import extract_firmware

        # Create a ZIP with only a dummy file
        zip_path = tmp_path / "bad_firmware.zip"
        dummy = tmp_path / "dummy.bin"
        dummy.write_bytes(b"\x00" * 16)
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(dummy, "dummy.bin")

        with pytest.raises(FileNotFoundError, match="flasher_args.json not found"):
            extract_firmware(str(zip_path))


class TestConfigureWriteFlashArgs:
    """Tests for configure_write_flash_args function."""

    def test_configure_basic(self, tmp_path, sample_flasher_args):
        """Verify EsptoolFlashArgs fields are correctly populated."""
        from esp_flasher.core.firmware import configure_write_flash_args

        # Create dummy bin files in tmp_path
        for name in ["bootloader.bin", "app.bin", "partition-table.bin"]:
            (tmp_path / name).write_bytes(b"\x00" * 16)

        result = configure_write_flash_args(sample_flasher_args, str(tmp_path))

        assert result.chip == "esp32s3"
        assert result.flash_mode == "dio"
        assert result.flash_freq == "80m"
        assert result.flash_size == "8MB"
        assert result.before == "default_reset"
        assert result.after == "hard_reset"
        assert result.no_stub is False  # stub=True → no_stub=False
        assert result.write_flash_args == [
            "--flash_mode", "dio", "--flash_freq", "80m", "--flash_size", "8MB"
        ]
        # Verify addr_filename contains absolute paths
        assert len(result.addr_filename) == 6  # 3 files × 2 (offset + path)
        for i in range(1, len(result.addr_filename), 2):
            assert os.path.isabs(result.addr_filename[i])

    def test_configure_no_stub(self, tmp_path, sample_flasher_args):
        """When stub is False, no_stub should be True."""
        from esp_flasher.core.firmware import configure_write_flash_args

        sample_flasher_args["extra_esptool_args"]["stub"] = False
        for name in ["bootloader.bin", "app.bin", "partition-table.bin"]:
            (tmp_path / name).write_bytes(b"\x00" * 16)

        result = configure_write_flash_args(sample_flasher_args, str(tmp_path))
        assert result.no_stub is True


class TestEnableSecureBoot:
    """Tests for enable_secure_boot function."""

    @patch("esp_flasher.core.firmware.espefuse")
    def test_secure_boot_success(self, mock_espefuse, tmp_path):
        """Successful secure boot burns key digest then enables SECURE_BOOT_EN."""
        from esp_flasher.core.firmware import enable_secure_boot

        # Create digest file
        digest_file = tmp_path / "digest.bin"
        digest_file.write_bytes(b"\x00" * 32)

        app_config = {"public_key_digest_block_index": 0}
        flasher_args = {"security": {"digest_file": "digest.bin"}}

        enable_secure_boot(app_config, "/dev/ttyUSB0", 460800, flasher_args, str(tmp_path))

        assert mock_espefuse.main.call_count == 2

        # First call: burn_key with digest
        first_args = mock_espefuse.main.call_args_list[0][0][0]
        assert "burn_key" in first_args
        assert "BLOCK_KEY0" in first_args
        assert str(digest_file) in first_args
        assert "SECURE_BOOT_DIGEST0" in first_args
        assert "--do-not-confirm" in first_args

        # Second call: burn_efuse SECURE_BOOT_EN
        second_args = mock_espefuse.main.call_args_list[1][0][0]
        assert "burn_efuse" in second_args
        assert "SECURE_BOOT_EN" in second_args

    def test_secure_boot_missing_block_index(self, tmp_path):
        """Missing public_key_digest_block_index raises EspFlasherError."""
        from esp_flasher.core.firmware import enable_secure_boot

        app_config = {"public_key_digest_block_index": None}
        with pytest.raises(EspFlasherError, match="Public key digest block not specified"):
            enable_secure_boot(app_config, "/dev/ttyUSB0", 460800, {}, str(tmp_path))

    @patch("esp_flasher.core.firmware.espefuse")
    def test_secure_boot_missing_digest_file(self, mock_espefuse, tmp_path):
        """Missing digest file raises EspFlasherError."""
        from esp_flasher.core.firmware import enable_secure_boot

        app_config = {"public_key_digest_block_index": 0}
        flasher_args = {"security": {"digest_file": "nonexistent.bin"}}

        with pytest.raises(EspFlasherError, match="Public key digest file not found"):
            enable_secure_boot(app_config, "/dev/ttyUSB0", 460800, flasher_args, str(tmp_path))


class TestEnableFlashEncryption:
    """Tests for enable_flash_encryption function."""

    @patch("esp_flasher.core.firmware.espefuse")
    @patch("esp_flasher.core.firmware.espsecure")
    def test_generate_key(self, mock_espsecure, mock_espefuse, tmp_path):
        """When not using customer key, generates key then burns it."""
        from esp_flasher.core.firmware import enable_flash_encryption

        # espsecure.main should create the key file as a side effect
        key_path = os.path.join(str(tmp_path), "flash_encrypt_key.bin")

        def create_key_file(args):
            with open(args[1], "wb") as f:
                f.write(b"\x00" * 32)

        mock_espsecure.main.side_effect = create_key_file

        app_config = {
            "flash_encryption_use_customer_key_enable": False,
            "encryption_key_block_index": 1,
        }

        enable_flash_encryption(app_config, "/dev/ttyUSB0", str(tmp_path))

        # espsecure should generate the key
        mock_espsecure.main.assert_called_once()
        gen_args = mock_espsecure.main.call_args[0][0]
        assert "generate_flash_encryption_key" in gen_args

        # espefuse should burn the key
        mock_espefuse.main.assert_called_once()
        burn_args = mock_espefuse.main.call_args[0][0]
        assert "burn_key" in burn_args
        assert "BLOCK_KEY1" in burn_args
        assert "XTS_AES_128_KEY" in burn_args

    @patch("esp_flasher.core.firmware.espefuse")
    @patch("esp_flasher.core.firmware.espsecure")
    def test_customer_key(self, mock_espsecure, mock_espefuse, tmp_path):
        """When using customer key, does NOT generate key, just burns the provided one."""
        from esp_flasher.core.firmware import enable_flash_encryption

        # Create the customer key file
        key_file = tmp_path / "customer_key.bin"
        key_file.write_bytes(b"\x00" * 32)

        app_config = {
            "flash_encryption_use_customer_key_enable": True,
            "flash_encryption_use_customer_key_path": str(key_file),
            "encryption_key_block_index": 2,
        }

        enable_flash_encryption(app_config, "/dev/ttyUSB0", str(tmp_path))

        # espsecure should NOT be called
        mock_espsecure.main.assert_not_called()

        # espefuse should burn the customer key
        mock_espefuse.main.assert_called_once()
        burn_args = mock_espefuse.main.call_args[0][0]
        assert "BLOCK_KEY2" in burn_args
        assert str(key_file) in burn_args

    def test_missing_block_index(self, tmp_path):
        """Missing encryption_key_block_index raises EspFlasherError."""
        from esp_flasher.core.firmware import enable_flash_encryption

        # Create a key file so we pass the file-exists check
        key_file = tmp_path / "key.bin"
        key_file.write_bytes(b"\x00" * 32)

        app_config = {
            "flash_encryption_use_customer_key_enable": True,
            "flash_encryption_use_customer_key_path": str(key_file),
            "encryption_key_block_index": None,
        }

        with pytest.raises(EspFlasherError, match="Encryption key block not specified"):
            enable_flash_encryption(app_config, "/dev/ttyUSB0", str(tmp_path))


class TestBurnAndProtectSecurityEfuses:
    """Tests for burn_and_protect_security_efuses function."""

    @patch("esp_flasher.core.firmware.espefuse")
    def test_burn_success(self, mock_espefuse):
        """Burns security eFuses and write-protects them."""
        from esp_flasher.core.firmware import burn_and_protect_security_efuses

        burn_and_protect_security_efuses("/dev/ttyUSB0")

        # 1 bulk burn_efuse call + 2 write_protect_efuse calls = 3 total
        assert mock_espefuse.main.call_count == 3

        # First call: burn_efuse with all security eFuses
        burn_args = mock_espefuse.main.call_args_list[0][0][0]
        assert "burn_efuse" in burn_args
        assert "DIS_DOWNLOAD_ICACHE" in burn_args
        assert "HARD_DIS_JTAG" in burn_args
        assert "DIS_DIRECT_BOOT" in burn_args
        assert "DIS_USB_JTAG" in burn_args
        assert "SECURE_BOOT_AGGRESSIVE_REVOKE" in burn_args
        assert "--port" in burn_args
        assert "/dev/ttyUSB0" in burn_args

        # Second call: write_protect_efuse DIS_ICACHE
        wp1_args = mock_espefuse.main.call_args_list[1][0][0]
        assert "write_protect_efuse" in wp1_args
        assert "DIS_ICACHE" in wp1_args

        # Third call: write_protect_efuse RD_DIS
        wp2_args = mock_espefuse.main.call_args_list[2][0][0]
        assert "write_protect_efuse" in wp2_args
        assert "RD_DIS" in wp2_args

    @patch("esp_flasher.core.firmware.espefuse")
    def test_burn_failure_raises(self, mock_espefuse):
        """When espefuse.main raises, exception should propagate."""
        from esp_flasher.core.firmware import burn_and_protect_security_efuses

        mock_espefuse.main.side_effect = RuntimeError("eFuse burn failed")

        with pytest.raises(RuntimeError, match="eFuse burn failed"):
            burn_and_protect_security_efuses("/dev/ttyUSB0")

    @patch("esp_flasher.core.firmware.espefuse")
    def test_write_protect_failure_raises(self, mock_espefuse):
        """When write-protect step fails, exception should propagate."""
        from esp_flasher.core.firmware import burn_and_protect_security_efuses

        # First call (burn) succeeds, second call (write_protect) fails
        mock_espefuse.main.side_effect = [None, RuntimeError("write-protect failed")]

        with pytest.raises(RuntimeError, match="write-protect failed"):
            burn_and_protect_security_efuses("/dev/ttyUSB0")

import json
import os
import zipfile

import pytest


@pytest.fixture
def sample_flasher_args():
    """Minimal flasher_args.json structure matching ESP-IDF build output."""
    return {
        "write_flash_args": ["--flash_mode", "dio", "--flash_freq", "80m", "--flash_size", "8MB"],
        "flash_settings": {
            "flash_mode": "dio",
            "flash_freq": "80m",
            "flash_size": "8MB",
        },
        "extra_esptool_args": {
            "chip": "esp32s3",
            "before": "default_reset",
            "after": "hard_reset",
            "stub": True,
        },
        "flash_files": {
            "0x0": "bootloader.bin",
            "0x10000": "app.bin",
            "0x8000": "partition-table.bin",
        },
        "security": {},
    }


@pytest.fixture
def sample_flasher_args_with_security():
    """Flasher args with security features enabled."""
    return {
        "write_flash_args": ["--flash_mode", "dio", "--flash_freq", "80m", "--flash_size", "8MB"],
        "flash_settings": {
            "flash_mode": "dio",
            "flash_freq": "80m",
            "flash_size": "8MB",
        },
        "extra_esptool_args": {
            "chip": "esp32s3",
            "before": "default_reset",
            "after": "hard_reset",
            "stub": True,
        },
        "flash_files": {
            "0x0": "bootloader.bin",
            "0x10000": "app.bin",
        },
        "security": {
            "secure_boot": True,
            "encryption": True,
            "digest_file": "digest.bin",
        },
    }


@pytest.fixture
def sample_config():
    """Config dict matching config/config.json structure."""
    return {
        "secure_boot": {
            "public_key_digest_block_index": 0,
        },
        "flash_encryption": {
            "encryption_en": False,
            "encryption_key_block_index": 1,
            "flash_encryption_use_customer_key_enable": False,
            "flash_encryption_use_customer_key_path": "keys/flash_encrypt_key.bin",
        },
        "printer_settings": {
            "default_printer": "Brother QL-600",
            "label_width": 62,
        },
        "chip_port": "/dev/ttyUSB0",
        "firmware_path": "",
        "api_settings": {
            "api_endpoint": "http://127.0.0.1:5000/publish",
            "api_key": "TEST_KEY",
            "api_secret": "TEST_SECRET",
        },
        "testing_settings": {
            "enabled": True,
            "test_board_xth_occurrence": 2,
            "test_success_regex": "Multicore\\s+app",
            "test_timeout_seconds": 10,
        },
    }


@pytest.fixture
def firmware_zip(tmp_path, sample_flasher_args):
    """Creates a minimal firmware ZIP file with flasher_args.json and dummy binaries."""
    # Create dummy binary files
    for name in ["bootloader.bin", "app.bin", "partition-table.bin"]:
        (tmp_path / name).write_bytes(b"\x00" * 64)

    # Write flasher_args.json
    flasher_args_path = tmp_path / "flasher_args.json"
    flasher_args_path.write_text(json.dumps(sample_flasher_args))

    # Create ZIP
    zip_path = tmp_path / "firmware.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(flasher_args_path, "flasher_args.json")
        for name in ["bootloader.bin", "app.bin", "partition-table.bin"]:
            zf.write(tmp_path / name, name)

    return str(zip_path)


@pytest.fixture
def firmware_zip_with_security(tmp_path, sample_flasher_args_with_security):
    """Creates a firmware ZIP with security files included."""
    for name in ["bootloader.bin", "app.bin", "digest.bin"]:
        (tmp_path / name).write_bytes(b"\x00" * 64)

    flasher_args_path = tmp_path / "flasher_args.json"
    flasher_args_path.write_text(json.dumps(sample_flasher_args_with_security))

    zip_path = tmp_path / "firmware_secure.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(flasher_args_path, "flasher_args.json")
        for name in ["bootloader.bin", "app.bin", "digest.bin"]:
            zf.write(tmp_path / name, name)

    return str(zip_path)

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



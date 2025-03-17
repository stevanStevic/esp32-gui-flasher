import json
import zipfile
import tempfile
import os

import espefuse
import espsecure

from esp_flasher.core.chip_utils import EsptoolFlashArgs
from esp_flasher.helpers.utils import load_config, Esp_flasherError


def extract_firmware(firmware_path):
    """
    Extracts a firmware ZIP file to a temporary directory and loads flasher_args.json.

    Args:
        firmware_path (str): Path to the firmware ZIP file.

    Returns:
        tuple: (dict, str) containing loaded JSON data from `flasher_args.json` and the temporary directory path.

    Raises:
        FileNotFoundError: If the firmware file or flasher_args.json is missing.
        json.JSONDecodeError: If flasher_args.json is not valid JSON.
    """
    if not os.path.exists(firmware_path):
        raise FileNotFoundError(f"Firmware file not found: {firmware_path}")

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Extract the ZIP file
    with zipfile.ZipFile(firmware_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    # Locate `flasher_args.json`
    flasher_args_path = os.path.join(temp_dir, "flasher_args.json")
    if not os.path.exists(flasher_args_path):
        raise FileNotFoundError("flasher_args.json not found in firmware package!")

    # Load `flasher_args.json`
    with open(flasher_args_path, "r") as f:
        flasher_args = json.load(f)

    return flasher_args, temp_dir


def enable_secure_boot(port, baud_rate, flasher_args, extract_dir):
    """Enables Secure Boot if configured and signs the firmware binaries."""

    secure_boot_config = load_config().get("secure_boot", {})
    if secure_boot_config is None:
        return  # Secure config not good, skip

    # Now check the actual release
    security = flasher_args.get("security", {})
    if security is None:
        return  # Security in release not enabled, skip

    # If release has security enabled then we need to specify block for digest flashing.
    # this can be extended to support multi-digest signing etc.
    if secure_boot_config.get("public_key_digest_block_index", None) is None:
        raise Esp_flasherError(f"Public key digest block not specified!")

    block_idx = secure_boot_config.get("public_key_digest_block_index")

    print("Enabling Secure Boot...")
    digest_path = security.get("digest_file", "")
    digest_file = os.path.join(extract_dir, digest_path)
    if not os.path.exists(digest_file):
        raise Esp_flasherError(f"Public key digest file not found: {digest_file}")

    # Burn the secure boot public key digest.
    espefuse.main(
        [
            "--do-not-confirm",
            "--chip",
            "auto",
            "--port",
            str(port),
            "--baud",
            str(baud_rate),
            "burn_key",
            f"BLOCK_KEY{block_idx}",
            digest_file,
            f"SECURE_BOOT_DIGEST0",
        ]
    )
    print("Secure boot eFuse burned with public key digest.")

    # Enable secure boot in eFuses
    espefuse.main(
        [
            "--do-not-confirm",
            "--port",
            str(port),
            "--chip",
            "auto",
            "burn_efuse",
            "SECURE_BOOT_EN",
        ]
    )
    print("Secure boot eFuse enabled successfully.")


def enable_flash_encryption(chip):
    """Enables Flash Encryption if configured."""
    flash_config = load_config().get("flash_encryption", {})

    if flash_config is None:
        return  # Encryption config not good, skip

    if not flash_config.get("flash_encryption_en", False):
        return  # Flash encryption not enabled, skip

    print("Enabling Flash Encryption...")
    key_path = flash_config.get("flash_encryption_use_customer_key_path")

    if not flash_config.get("flash_encryption_use_customer_key_enable", False):
        # Generate encryption key if not user-specified
        key_path = "generated_flash_encrypt_key.bin"
        espsecure.main(["generate_flash_encryption_key", key_path])

    if not os.path.exists(key_path):
        raise Esp_flasherError(f"Flash encryption key not found: {key_path}")

    # Flash encryption key using espefuse
    espefuse.main(["--chip", chip.CHIP_NAME, "burn_key", "flash_encryption", key_path])

    print("Flash Encryption enabled successfully.")


def configure_write_flash_args(flasher_args, extract_dir):
    """
    Extracts firmware ZIP, reads `flasher_args.json`, and constructs flashing arguments.

    Args:
        flasher_args (str): JSON with extract flashing arguments from firmware release
    Returns:
        dict: Contains flash mode, flash frequency, and list of (offset, file) tuples.
    """

    # Extract flash arguments
    write_flash_args = flasher_args["write_flash_args"]
    flash_mode = flasher_args["flash_settings"]["flash_mode"]
    flash_freq = flasher_args["flash_settings"]["flash_freq"]
    flash_size = flasher_args["flash_settings"]["flash_size"]
    stub = flasher_args.get("extra_esptool_args", {}).get("stub", True)
    chip = flasher_args["extra_esptool_args"]["chip"]
    before = flasher_args["extra_esptool_args"]["before"]
    after = flasher_args["extra_esptool_args"]["after"]

    # Prepare list of (offset, filename) tuples
    flash_files = flasher_args["flash_files"]
    addr_filename = []
    for offset, relative_path in flash_files.items():
        abs_path = os.path.join(extract_dir, relative_path)
        try:
            addr_filename.append(offset)
            addr_filename.append(abs_path)
        except ValueError:
            raise ValueError(f"Invalid offset format: {offset}")

    # Return structured arguments
    return EsptoolFlashArgs(
        chip,
        write_flash_args,
        flash_size,
        addr_filename,
        flash_mode,
        flash_freq,
        stub,
        before,
        after,
    )

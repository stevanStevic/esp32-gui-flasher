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


def enable_secure_boot(app_config, port, baud_rate, flasher_args, extract_dir):
    """
    Enables Secure Boot if configured and signs the firmware binaries.

    More details: https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/security/host-based-security-workflows.html#introduction
    """

    print("Enabling Secure Boot...")

    # If release has security enabled then we need to specify block for digest flashing.
    # this can be extended to support multi-digest signing etc.
    if app_config.get("public_key_digest_block_index", None) is None:
        raise Esp_flasherError(f"Public key digest block not specified!")

    block_idx = app_config.get("public_key_digest_block_index")

    digest_path = flasher_args.get("security", {}).get("digest_file", "")
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


def enable_flash_encryption(app_config, port, extract_dir):
    """
    Enables Flash Encryption if configured.

    More details: https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/security/host-based-security-workflows.html#introduction
    """

    print("Enabling Flash Encryption...")

    key_file = ""
    if app_config.get("flash_encryption_use_customer_key_enable", False):
        key_file = app_config.get("flash_encryption_use_customer_key_path")
    else:
        # Generate encryption key if not user-specified
        key_file = os.path.join(extract_dir, "flash_encrypt_key.bin")
        espsecure.main(["generate_flash_encryption_key", key_file])

    if not os.path.exists(key_file):
        raise Esp_flasherError(f"Flash encryption key not found: {key_file}")

    # If release has encryption enabled then we need to specify block for encryption key.
    # This can be extended to support multi encryption keys.
    if app_config.get("encryption_key_block_index", None) is None:
        raise Esp_flasherError(f"Encryption key block not specified!")

    block_idx = app_config.get("encryption_key_block_index")

    # Flash encryption key using espefuse
    espefuse.main(
        [
            "--do-not-confirm",
            "--port",
            str(port),
            "burn_key",
            f"BLOCK_KEY{block_idx}",
            key_file,
            "XTS_AES_128_KEY",
        ]
    )

    print("Flash Encryption key flashed successfully.")


def burn_and_protect_security_efuses(port):
    """
    Burns multiple security eFuses and applies write protection to prevent modification.
    More details: https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/security/host-based-security-workflows.html#introduction

    Args:
        port (str): Serial port of the ESP32S3 device (e.g., "/dev/ttyUSB0").

    Raises:
        Exception: If the eFuse burning process fails.
    """

    # eFuses to burn (security settings)
    security_efuses = {
        "DIS_DOWNLOAD_ICACHE": "0x1",  # Disable UART instruction cache
        "DIS_DOWNLOAD_DCACHE": "0x1",  # Disable UART data cache
        "HARD_DIS_JTAG": "0x1",  # Hard disable JTAG peripheral
        "SOFT_DIS_JTAG": "0x1",  # Disable software access to JTAG
        "DIS_DIRECT_BOOT": "0x1",  # Disable direct boot (legacy SPI boot mode)
        "DIS_USB_JTAG": "0x1",  # Disable USB switch to JTAG
        "DIS_DOWNLOAD_MANUAL_ENCRYPT": "0x1",  # Disable UART bootloader encryption access
        "SECURE_BOOT_AGGRESSIVE_REVOKE": "0x1",  # Aggressive revocation of key digests
    }

    print("Burning security eFuses...")

    # Construct a single espefuse command with all eFuses
    burn_command = [
        "--do-not-confirm",
        "--port",
        str(port),
        "burn_efuse",
    ]

    # Append each eFuse and its value
    for efuse, value in security_efuses.items():
        burn_command.append(efuse)
        burn_command.append(value)

    print("Running eFuse burning command:")
    print(f"espefuse.py {' '.join(burn_command)}")

    try:
        espefuse.main(burn_command)
        print("All security eFuses burned successfully.")
    except Exception as e:
        print(f"Error while burning eFuses: {e}")
        raise

    # **Step 2: Write-Protect Security eFuses**
    print("\nApplying write protection to security eFuses...")

    write_protect_efuses = [
        "DIS_ICACHE",  # Write-protects multiple security configurations
        "RD_DIS",  # Prevents accidental read protection of Secure Boot digest
    ]

    for efuse in write_protect_efuses:
        print(f"Writing protection for {efuse}...")
        try:
            espefuse.main(
                [
                    "--do-not-confirm",
                    "--port",
                    str(port),
                    "write_protect_efuse",
                    efuse,
                ]
            )
            print(f"{efuse} write-protected successfully.")
        except Exception as e:
            print(f"Failed to write-protect {efuse}: {e}")
            raise

    print("\nSecurity eFuses burned and write-protected successfully.")


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

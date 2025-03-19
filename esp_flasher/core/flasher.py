import esptool

from esp_flasher.core.firmware_utils import (
    extract_firmware,
    enable_secure_boot,
    enable_flash_encryption,
    configure_write_flash_args,
)
from esp_flasher.helpers.utils import Esp_flasherError


def run_esp_flasher(port, firmware, baud_rate=115200, no_erase=True):
    """Runs the ESP flashing process, integrating secure boot and encryption."""

    flasher_args, extract_dir = extract_firmware(firmware_path=firmware)
    firmware_args = configure_write_flash_args(flasher_args, extract_dir)

    # Now check the configuration from the actual release
    encryption_enabled = flasher_args.get("security", {}).get("encryption", False)
    if encryption_enabled:
        enable_flash_encryption(port, flasher_args, extract_dir)

    # Now check the configuration from the actual release
    secure_boot_enabled = flasher_args.get("security", {}).get("secure_boot", False)
    if secure_boot_enabled:
        enable_secure_boot(port, baud_rate, flasher_args, extract_dir)

    # Base esptool command
    esptool_cmd = [
        "--chip",
        firmware_args.chip,
        "--port",
        port,
        "--baud",
        str(baud_rate),
        "--before",
        firmware_args.before,
        "--after",
        firmware_args.after,
    ]

    # Check if we should disable the stub loader
    if firmware_args.no_stub:
        esptool_cmd.append("--no-stub")

    # Add flash arguments
    esptool_cmd.extend(["write_flash"] + firmware_args.write_flash_args)

    # Add flash file commands
    esptool_cmd.extend(firmware_args.addr_filename)

    try:
        esptool.main(esptool_cmd)

        # Burn the security fuses and write protect
        if encryption_enabled and secure_boot_enabled:
            burn_and_protect_security_efuses(port)

    except esptool.FatalError as err:
        raise Esp_flasherError(f"Error while writing flash: {err}")
    except Exception as e:
        print("Flash error:", e)

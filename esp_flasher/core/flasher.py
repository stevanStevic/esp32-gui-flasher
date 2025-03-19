import esptool

from esp_flasher.core.firmware_utils import (
    burn_and_protect_security_efuses,
    extract_firmware,
    enable_secure_boot,
    enable_flash_encryption,
    configure_write_flash_args,
)
from esp_flasher.helpers.utils import Esp_flasherError, load_config


def run_esp_flasher(port, firmware, baud_rate=115200):
    """Runs the ESP flashing process, integrating secure boot and encryption."""

    app_config = load_config()
    flasher_args, extract_dir = extract_firmware(firmware_path=firmware)
    firmware_args = configure_write_flash_args(flasher_args, extract_dir)

    app_encryption_enabled = app_config.get("flash_encryption", {}).get(
        "encryption_en", False
    )
    release_encryption_enabled = flasher_args.get("security", {}).get(
        "encryption", False
    )
    encryption_enabled = app_encryption_enabled or release_encryption_enabled
    if encryption_enabled:
        enable_flash_encryption(
            app_config.get("flash_encryption", {}), port, extract_dir
        )

    # Now check the configuration from the actual release
    secure_boot_enabled = flasher_args.get("security", {}).get("secure_boot", False)
    if secure_boot_enabled:
        enable_secure_boot(
            app_config.get("secure_boot", {}),
            port,
            baud_rate,
            flasher_args,
            extract_dir,
        )

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

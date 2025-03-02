import json
import zipfile
import tempfile
import os

from esp_flasher.core.chip_utils import MockEsptoolArgs
from esp_flasher.helpers.helpers import open_downloadable_binary


def configure_write_flash_args(firmware_path):
    """
    Extracts firmware ZIP, reads `flasher_args.json`, and constructs flashing arguments.

    Args:
        firmware_path (str): Path to the firmware ZIP file.

    Returns:
        dict: Contains flash mode, flash frequency, and list of (offset, file) tuples.
    """

    if not os.path.exists(firmware_path):
        raise FileNotFoundError(f"Firmware file not found: {firmware_path}")

    # Extract ZIP to a temporary directory
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(firmware_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    # Locate `flasher_args.json`
    flasher_args_path = os.path.join(temp_dir, "flasher_args.json")
    if not os.path.exists(flasher_args_path):
        raise FileNotFoundError("flasher_args.json not found in firmware package!")

    # Load flasher_args.json
    with open(flasher_args_path, "r") as f:
        flasher_args = json.load(f)

    # Extract flash mode, frequency, and files
    flash_mode = flasher_args["flash_settings"]["flash_mode"]
    flash_freq = flasher_args["flash_settings"]["flash_freq"]
    flash_size = flasher_args["flash_settings"]["flash_size"]
    flash_files = flasher_args["flash_files"]

    # Prepare list of (offset, filename) tuples
    addr_filename = []
    for offset, relative_path in flash_files.items():
        abs_path = os.path.join(temp_dir, relative_path)
        try:
            binary = open_downloadable_binary(abs_path)
            offset_int = int(offset, 16)  # Convert offset from string to hex integer
            addr_filename.append((offset_int, binary))
        except ValueError:
            raise ValueError(f"Invalid offset format: {offset}")

    # Return structured arguments
    return MockEsptoolArgs(flash_size, addr_filename, flash_mode, flash_freq)

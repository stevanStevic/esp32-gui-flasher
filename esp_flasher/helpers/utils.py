import datetime
import io
import os
import sys

import serial

from esp_flasher.core.const import HTTP_REGEX
from esp_flasher.core.errors import EspFlasherError

# pylint: disable=unspecified-encoding,consider-using-with
DEVNULL = open(os.devnull, "w")


def open_downloadable_binary(path):
    if hasattr(path, "seek"):
        path.seek(0)
        return path

    if HTTP_REGEX.match(path) is not None:
        import requests

        try:
            response = requests.get(path)
            response.raise_for_status()
        except requests.exceptions.Timeout as err:
            raise EspFlasherError(
                f"Timeout while retrieving firmware file '{path}': {err}"
            ) from err
        except requests.exceptions.RequestException as err:
            raise EspFlasherError(
                f"Error while retrieving firmware file '{path}': {err}"
            ) from err

        binary = io.BytesIO()
        binary.write(response.content)
        binary.seek(0)
        return binary

    try:
        return open(path, "rb")
    except IOError as err:
        raise EspFlasherError(f"Error opening binary '{path}': {err}") from err


def prevent_print(func, *args, **kwargs):
    orig_sys_stdout = sys.stdout
    sys.stdout = DEVNULL
    try:
        return func(*args, **kwargs)
    except serial.SerialException as err:
        raise EspFlasherError("Serial port closed: {}".format(err)) from err
    finally:
        sys.stdout = orig_sys_stdout


def get_device_dir(device_name=None, mac_address=None):
    """Generate a directory path based on device name, mac address, or 'unknown'."""
    if device_name:
        dir_name = device_name
    elif mac_address:
        dir_name = mac_address.replace(":", "_")
    else:
        dir_name = "unknown"
    base_dir = os.getcwd()
    device_dir = os.path.join(base_dir, dir_name)
    os.makedirs(device_dir, exist_ok=True)
    return device_dir


def get_log_path(device_dir, prefix):
    """Generate a unique log file path with the given prefix."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(device_dir, f"{prefix}_{timestamp}.log")


def get_flash_log_path(device_dir):
    """Generate a unique log file path for flashing."""
    return get_log_path(device_dir, "flashing")


def get_testing_log_path(device_dir):
    """Generate a unique log file path for testing."""
    return get_log_path(device_dir, "testing")

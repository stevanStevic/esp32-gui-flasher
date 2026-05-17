import datetime
import os
import sys

import serial

from esp_flasher.core.errors import EspFlasherError

_DEVNULL = open(os.devnull, "w")  # noqa: SIM115


def prevent_print(func, *args, **kwargs):
    """Call *func* while suppressing stdout (used to silence esptool)."""
    orig_sys_stdout = sys.stdout
    sys.stdout = _DEVNULL
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

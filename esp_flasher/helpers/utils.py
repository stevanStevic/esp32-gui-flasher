import datetime
import io
import json
import os
import sys

import serial


class Esp_flasherError(Exception):
    pass


from esp_flasher.core.const import HTTP_REGEX

# pylint: disable=unspecified-encoding,consider-using-with
DEVNULL = open(os.devnull, "w")
CONFIG_PATH = "config/config.json"


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
            raise Esp_flasherError(
                f"Timeout while retrieving firmware file '{path}': {err}"
            ) from err
        except requests.exceptions.RequestException as err:
            raise Esp_flasherError(
                f"Error while retrieving firmware file '{path}': {err}"
            ) from err

        binary = io.BytesIO()
        binary.write(response.content)
        binary.seek(0)
        return binary

    try:
        return open(path, "rb")
    except IOError as err:
        raise Esp_flasherError(f"Error opening binary '{path}': {err}") from err


def prevent_print(func, *args, **kwargs):
    orig_sys_stdout = sys.stdout
    sys.stdout = DEVNULL
    try:
        return func(*args, **kwargs)
    except serial.SerialException as err:
        from esp_flasher.core.chip_utils import EspflasherError

        raise EspflasherError("Serial port closed: {}".format(err))
    finally:
        sys.stdout = orig_sys_stdout
        sys.stdout.isatty = lambda: False
        pass


def load_config(path=CONFIG_PATH):
    """Loads configuration from the .config JSON file."""
    if not os.path.exists(path):
        raise Esp_flasherError(f"Config file {path} not found.")

    try:
        with open(path, "r") as config_file:
            config = json.load(config_file)
            return config
    except json.JSONDecodeError as e:
        raise Esp_flasherError(f"Error parsing config file: {e}")


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


def get_flash_log_path(device_dir):
    """Generate a unique log file path for flashing."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(device_dir, f"flashing_{timestamp}.log")


def get_testing_log_path(device_dir):
    """Generate a unique log file path for testing."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(device_dir, f"testing_{timestamp}.log")

import json
import os

from esp_flasher.core.errors import EspFlasherError

CONFIG_PATH = "config/config.json"


def load_config(path=CONFIG_PATH):
    """Loads configuration from the .config JSON file."""
    if not os.path.exists(path):
        raise EspFlasherError(f"Config file {path} not found.")

    try:
        with open(path, "r") as config_file:
            config = json.load(config_file)
            return config
    except json.JSONDecodeError as e:
        raise EspFlasherError(f"Error parsing config file: {e}")

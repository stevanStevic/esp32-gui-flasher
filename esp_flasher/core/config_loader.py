import json
import os

CONFIG_PATH = "config/.config"


def load_config():
    """Loads configuration from the .config JSON file."""
    if not os.path.exists(CONFIG_PATH):
        print("Config file not found, using defaults.")
        return {}

    try:
        with open(CONFIG_PATH, "r") as config_file:
            config = json.load(config_file)
            return config
    except json.JSONDecodeError as e:
        print(f"Error parsing config file: {e}")
        return {}


def apply_config_to_gui(gui):
    """Applies loaded config values to GUI elements."""
    config = load_config()

    # Apply printer settings
    printer_settings = config.get("printer_settings", {})
    gui.printer_config.printer_combobox.setCurrentText(
        printer_settings.get("default_printer", "")
    )
    gui.printer_config.width_spinbox.setValue(printer_settings.get("label_width", 62))
    gui.printer_config.font_size_spinbox.setValue(printer_settings.get("font_size", 20))
    gui.printer_config.rotation_spinbox.setValue(
        printer_settings.get("text_rotation", 270)
    )
    gui.printer_config.x_offset_spinbox.setValue(printer_settings.get("x_offset", 100))
    gui.printer_config.y_offset_spinbox.setValue(printer_settings.get("y_offset", 100))

    # Apply chip port and firmware path
    gui.port_config.chip_port_combobox.setCurrentText(config.get("chip_port", ""))
    gui.firmware_section.firmware_button.setText(config.get("firmware_path", ""))

    # Apply API settings
    api_settings = config.get("api_settings", {})
    gui.backend_config.line_edits["_api_endpoint"].setText(
        api_settings.get("api_endpoint", "")
    )
    gui.backend_config.line_edits["_api_key"].setText(api_settings.get("api_key", ""))
    gui.backend_config.line_edits["_api_secret"].setText(
        api_settings.get("api_secret", "")
    )

    print("Configuration applied to GUI.")

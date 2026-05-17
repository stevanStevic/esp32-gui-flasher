"""Built-in GUI module: Device Registration and Printing.

This module adds backend connection, printer setup, device registration
and label printing capabilities to the ESP32-GUI-Flasher.

Load with:
    python -m esp_flasher --gui --load-module esp_flasher/modules/registration_printing
"""

import logging

from esp_flasher.gui.module_base import GUIModule
from esp_flasher.modules.registration_printing.section import RegistrationPrintingSection

logger = logging.getLogger(__name__)


class RegistrationPrintingModule(GUIModule):
    """Adds backend connection, printer setup, device registration and
    label printing to the GUI."""

    def __init__(self):
        self._section = None

    def get_name(self) -> str:
        return "Device Registration and Printing"

    def create_section(self, state):
        self._section = RegistrationPrintingSection(state)
        return self._section

    def apply_config(self, config: dict) -> None:
        if self._section is None:
            return

        # Printer settings
        printer_settings = config.get("printer_settings", {})
        self._section.printer_combobox.setCurrentText(
            printer_settings.get("default_printer", "")
        )
        self._section.width_spinbox.setValue(
            printer_settings.get("label_width", 62)
        )
        self._section.font_size_spinbox.setValue(
            printer_settings.get("font_size", 20)
        )
        self._section.rotation_spinbox.setValue(
            printer_settings.get("text_rotation", 270)
        )
        self._section.x_offset_spinbox.setValue(
            printer_settings.get("x_offset", 100)
        )
        self._section.y_offset_spinbox.setValue(
            printer_settings.get("y_offset", 100)
        )

        # API / backend settings
        api_settings = config.get("api_settings", {})
        self._section.line_edits["api_endpoint"].setText(
            api_settings.get("api_endpoint", "")
        )
        self._section.line_edits["api_key"].setText(
            api_settings.get("api_key", "")
        )
        self._section.line_edits["api_secret"].setText(
            api_settings.get("api_secret", "")
        )

    def dispose(self) -> None:
        if self._section is None:
            return

        # Stop any running threads gracefully
        for attr in ("print_thread", "register_thread"):
            thread = getattr(self._section, attr, None)
            if thread is not None and thread.isRunning():
                logger.info(f"Stopping {attr}...")
                thread.quit()
                thread.wait(2000)

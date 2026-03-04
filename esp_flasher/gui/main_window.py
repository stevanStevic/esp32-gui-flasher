import sys
import logging

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QTextEdit,
)
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5.QtWidgets import QMessageBox

from esp_flasher.gui.port_config import PortConfig
from esp_flasher.gui.chip_info import ChipInfoSection
from esp_flasher.gui.firmware_section import FirmwareSection
from esp_flasher.gui.actions_section import ActionsSection
from esp_flasher.gui.module_loader import load_modules
from esp_flasher.helpers.utils import load_config
from esp_flasher.core.const import __version__
from esp_flasher.helpers.log_handler import FlashLogHandler, StdoutRedirector
from esp_flasher.model.test_module import TestModule
from esp_flasher.helpers.resource_helper import resource_path

logger = logging.getLogger(__name__)


def show_popup(title, message, icon, parent=None):
    """Displays an popup with the given message."""
    msg = QMessageBox(parent)
    msg.setIcon(icon)
    msg.setText(message)
    msg.setWindowIcon(QIcon(resource_path("icon.ico")))
    msg.setWindowTitle(title)
    msg.exec_()


class MainWindow(QMainWindow):
    def __init__(self, module_paths=None):
        super().__init__()
        import sys
        import traceback

        def excepthook(type, value, tb):
            traceback.print_exception(type, value, tb)
            sys.__excepthook__(type, value, tb)

        sys.excepthook = excepthook

        self._module_paths = module_paths or []
        self._modules = []
        self._firmware = None
        self._chip_port = None
        self._printer_port = None
        self._api_endpoint = ""
        self._api_key = ""
        self._api_secret = ""
        self._mac_address = None
        self._device_name = ""
        self._successful_flash_count = 0
        self._testing_enabled = False
        self._test_board_xth_occurrence = 0
        self._test_success_regex = ""
        self._is_testing_active = False
        self._test_timeout_seconds = 30
        self.test_module = None

        self.init_ui()

        self.log_handler = FlashLogHandler(text_edit=None)
        logging.basicConfig(level=logging.INFO, handlers=[self.log_handler])
        logging.getLogger().addHandler(self.log_handler)
        self.log_handler.text_edit = self.console
        sys.stdout = StdoutRedirector(logging.getLogger(), logging.INFO)
        sys.stderr = StdoutRedirector(logging.getLogger(), logging.ERROR)

        self.apply_config_to_gui()
        self.apply_dark_theme()

    def apply_config_to_gui(self):
        """Applies loaded config values to GUI elements."""
        config = load_config()

        # Let each loaded module apply its own config
        for module in self._modules:
            try:
                module.apply_config(config)
            except Exception as exc:
                logger.error(f"Module '{module.get_name()}' failed to apply config: {exc}")

        # Apply chip port and firmware path
        self.port_config.chip_port_combobox.setCurrentText(config.get("chip_port", ""))
        self._firmware = config.get("firmware_path", "")
        self.firmware_section.firmware_button.setText(self._firmware)

        # Apply testing settings
        testing_settings = config.get("testing_settings", {})
        self._testing_enabled = testing_settings.get("enabled", False)
        self._test_board_xth_occurrence = testing_settings.get(
            "test_board_xth_occurrence", 0
        )
        self._test_success_regex = testing_settings.get("test_success_regex", "")
        self._test_timeout_seconds = testing_settings.get("test_timeout_seconds", 200)

        # Instantiate the model with latest config
        self.test_module = TestModule(
            self._test_success_regex,
            self._test_timeout_seconds,
            self._testing_enabled,
            self._test_board_xth_occurrence,
        )

    def init_ui(self):
        title = f"ESP32-GUI-Flasher {__version__}"
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal layout
        main_layout = QHBoxLayout()

        # Left vertical layout for controls
        left_layout_widget = QWidget()
        left_layout = QVBoxLayout()

        self.port_config = PortConfig(self)
        self.chip_info_section = ChipInfoSection(self)
        self.firmware_section = FirmwareSection(self)
        self.actions_section = ActionsSection(self)

        # Connect the flash button (now in firmware_section) to actions_section.flash_esp
        self.firmware_section.flash_button.clicked.connect(self.actions_section.flash_esp)

        # Order: Port Config -> Chip Info -> [Loaded Modules] -> Firmware -> Actions
        left_layout.addWidget(self.port_config)
        left_layout.addWidget(self.chip_info_section)

        # Load and insert extension modules
        if self._module_paths:
            try:
                self._modules = load_modules(self._module_paths)
            except Exception as exc:
                logger.error(f"Failed to load modules: {exc}")
                self._modules = []

            for module in self._modules:
                try:
                    section = module.create_section(self)
                    left_layout.addWidget(section)
                    logger.info(f"Module section added: {module.get_name()}")
                except Exception as exc:
                    logger.error(
                        f"Module '{module.get_name()}' failed to create section: {exc}"
                    )

        left_layout.addWidget(self.firmware_section)
        left_layout.addWidget(self.actions_section)
        left_layout.addStretch()
        left_layout_widget.setLayout(left_layout)

        # Console on the right
        self.console_group_box = QGroupBox("Console")
        console_layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        console_layout.addWidget(self.console)
        self.console_group_box.setLayout(console_layout)

        # Add left and right sections to the main layout
        main_layout.addWidget(left_layout_widget, 1)
        main_layout.addWidget(self.console_group_box, 1)

        central_widget.setLayout(main_layout)

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        self.setPalette(palette)

    def show_testing_popup(self, message):
        """Displays a non-blocking informational popup indicating that testing is in progress."""
        if hasattr(self, "testing_popup") and self.testing_popup is not None:
            self.testing_popup.close()
        self.testing_popup = QMessageBox(self)
        self.testing_popup.setIcon(QMessageBox.Warning)
        self.testing_popup.setText(message)
        self.testing_popup.setWindowTitle("Testing")
        self.testing_popup.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.testing_popup.setStandardButtons(QMessageBox.NoButton)
        self.testing_popup.show()

    def close_testing_popup(self):
        """Closes the testing popup if it is open and visible."""
        if hasattr(self, "testing_popup") and self.testing_popup is not None:
            try:
                if self.testing_popup.isVisible():
                    self.testing_popup.done(0)  # Force close
            except RuntimeError:
                pass  # Already deleted
            self.testing_popup = None

    def show_error_popup(self, message):
        """Displays an error popup with the given message."""
        show_popup("Error", message, QMessageBox.Critical)

    def show_success_popup(self, message):
        """Displays a success popup with the given message."""
        show_popup("Success", message, QMessageBox.Information)

    def set_log_file(self, file_path):
        if self.log_handler:
            self.log_handler.set_log_file(file_path)

    def close_log_file(self):
        if self.log_handler:
            self.log_handler.close()

    def closeEvent(self, event):
        """Dispose all loaded modules before closing."""
        for module in self._modules:
            try:
                module.dispose()
            except Exception as exc:
                logger.error(f"Module '{module.get_name()}' dispose failed: {exc}")
        super().closeEvent(event)

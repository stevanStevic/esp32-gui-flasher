import sys
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,  # Add QHBoxLayout
    QGroupBox,
    QTextEdit,
)
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5.QtWidgets import QMessageBox

from esp_flasher.gui.printer_config import PrinterConfig
from esp_flasher.gui.port_config import PortConfig
from esp_flasher.gui.backend_config import BackendConfig
from esp_flasher.gui.chip_info import ChipInfoSection
from esp_flasher.gui.firmware_section import FirmwareSection
from esp_flasher.gui.actions_section import ActionsSection
from esp_flasher.helpers.redirect_text import RedirectText
from esp_flasher.helpers.utils import load_config
from esp_flasher.core.const import __version__


def show_error_popup(message, parent=None):
    """Displays an error popup with the given message."""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setText(message)
    msg.setWindowTitle("Error")
    msg.exec_()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._firmware = None
        self._chip_port = None
        self._printer_port = None
        self._api_endpoint = ""
        self._api_key = ""
        self._api_secret = ""
        self._mac_address = None
        self._device_name = ""

        self.init_ui()
        self.apply_config_to_gui()  # Load configuration into GUI
        self.apply_dark_theme()
        sys.stdout = RedirectText(self.console)  # Redirect stdout to console

    def apply_config_to_gui(self):
        """Applies loaded config values to GUI elements."""
        config = load_config()

        # Apply printer settings
        printer_settings = config.get("printer_settings", {})
        self.printer_config.printer_combobox.setCurrentText(
            printer_settings.get("default_printer", "")
        )
        self.printer_config.width_spinbox.setValue(
            printer_settings.get("label_width", 62)
        )
        self.printer_config.font_size_spinbox.setValue(
            printer_settings.get("font_size", 20)
        )
        self.printer_config.rotation_spinbox.setValue(
            printer_settings.get("text_rotation", 270)
        )
        self.printer_config.x_offset_spinbox.setValue(
            printer_settings.get("x_offset", 100)
        )
        self.printer_config.y_offset_spinbox.setValue(
            printer_settings.get("y_offset", 100)
        )

        # Apply chip port and firmware path
        self.port_config.chip_port_combobox.setCurrentText(config.get("chip_port", ""))
        self._firmware = config.get("firmware_path", "")
        self.firmware_section.firmware_button.setText(self._firmware)

        # Apply API settings
        api_settings = config.get("api_settings", {})
        self.backend_config.line_edits["_api_endpoint"].setText(
            api_settings.get("api_endpoint", "")
        )
        self.backend_config.line_edits["_api_key"].setText(
            api_settings.get("api_key", "")
        )
        self.backend_config.line_edits["_api_secret"].setText(
            api_settings.get("api_secret", "")
        )

        print("Configuration applied to self.")

    def init_ui(self):
        self.setWindowTitle(f"ESP32-GUI-Flasher with Printer Support {__version__}")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icon.ico"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal layout
        main_layout = QHBoxLayout()

        # Left vertical layout for controls
        left_layout_widget = QWidget()
        left_layout = QVBoxLayout()

        self.port_config = PortConfig(self)
        self.printer_config = PrinterConfig(self)
        self.backend_config = BackendConfig(self)
        self.chip_info_section = ChipInfoSection(self)
        self.firmware_section = FirmwareSection(self)
        self.actions_section = ActionsSection(self)

        left_layout.addWidget(self.port_config)
        left_layout.addWidget(self.printer_config)
        left_layout.addWidget(self.backend_config)
        left_layout.addWidget(self.chip_info_section)
        left_layout.addWidget(self.firmware_section)
        left_layout.addWidget(self.actions_section)
        left_layout.addStretch()  # Add stretch to push widgets to the top
        left_layout_widget.setLayout(left_layout)

        # Console on the right
        self.console_group_box = QGroupBox("Console")
        console_layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        console_layout.addWidget(self.console)
        self.console_group_box.setLayout(console_layout)

        # Add left and right sections to the main layout
        main_layout.addWidget(left_layout_widget, 1)  # Assign a stretch factor of 1
        main_layout.addWidget(self.console_group_box, 1)  # Assign a stretch factor of 1

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

    def show_message(self, message):
        """Displays messages in the console."""
        self.console.append(message)  # Display the message in the UI console

    def show_colored_message(self, message, color):
        """Displays log messages in different colors based on log level."""
        self.console.setTextColor(QColor(color))
        self.console.append(message)
        self.console.setTextColor(QColor("white"))  # Reset color after printing

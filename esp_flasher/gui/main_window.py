import sys
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QTextEdit,
)
from PyQt5.QtGui import QIcon, QColor, QPalette

from esp_flasher.gui.printer_config import PrinterConfig
from esp_flasher.gui.port_config import PortConfig
from esp_flasher.gui.backend_config import BackendConfig
from esp_flasher.gui.chip_info import ChipInfoSection
from esp_flasher.gui.firmware_section import FirmwareSection
from esp_flasher.gui.actions_section import ActionsSection
from esp_flasher.helpers.redirect_text import RedirectText
from esp_flasher.core.const import __version__
from esp_flasher.core.config_loader import apply_config_to_gui


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
        apply_config_to_gui(self)  # Load configuration into GUI
        self.apply_dark_theme()
        sys.stdout = RedirectText(self.console)  # Redirect stdout to console

    def init_ui(self):
        self.setWindowTitle(f"ESP32-GUI-Flasher with Printer Support {__version__}")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icon.ico"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.port_config = PortConfig(self)
        self.printer_config = PrinterConfig(self)
        self.backend_config = BackendConfig(self)
        self.chip_info_section = ChipInfoSection(self)
        self.firmware_section = FirmwareSection(self)
        self.actions_section = ActionsSection(self)

        self.console_group_box = QGroupBox("Console")
        console_layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        console_layout.addWidget(self.console)
        self.console_group_box.setLayout(console_layout)

        layout.addWidget(self.port_config)
        layout.addWidget(self.printer_config)
        layout.addWidget(self.backend_config)
        layout.addWidget(self.chip_info_section)
        layout.addWidget(self.firmware_section)
        layout.addWidget(self.actions_section)
        layout.addWidget(self.console_group_box)

        central_widget.setLayout(layout)

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

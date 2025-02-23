# Big thx to Michael Kandziora for this GUI port to PyQt5
import re
import sys
import threading
import os
import platform
import distro


from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QFileDialog,
    QTextEdit,
    QGroupBox,
    QGridLayout,
    QLineEdit,
)
from PyQt5.QtGui import QColor, QTextCursor, QPalette, QColor, QIcon
from PyQt5.QtCore import pyqtSignal, QObject, QThread

from esp_flasher.helpers import list_serial_ports
from esp_flasher.const import __version__

COLOR_RE = re.compile(r"(?:\033)(?:\[(.*?)[@-~]|\].*?(?:\007|\033\\))")
COLORS = {
    "black": QColor("black"),
    "red": QColor("red"),
    "green": QColor("green"),
    "yellow": QColor("yellow"),
    "blue": QColor("blue"),
    "magenta": QColor("magenta"),
    "cyan": QColor("cyan"),
    "white": QColor("white"),
}
FORE_COLORS = {**COLORS, None: QColor("white")}
BACK_COLORS = {**COLORS, None: QColor("black")}


class RedirectText(QObject):
    text_written = pyqtSignal(str)

    def __init__(self, text_edit):
        super().__init__()
        self._out = text_edit
        self._line = ""
        self._bold = False
        self._italic = False
        self._underline = False
        self._foreground = None
        self._background = None
        self._secret = False
        self.text_written.connect(self._append_text)

    def write(self, string):
        self.text_written.emit(string)

    def flush(self):
        pass

    def _append_text(self, text):
        cursor = self._out.textCursor()
        self._out.moveCursor(QTextCursor.End)
        self._out.insertPlainText(text)
        self._out.setTextCursor(cursor)


class FlashingThread(threading.Thread):
    def __init__(self, firmware, port):
        threading.Thread.__init__(self)
        self.daemon = True
        self._firmware = firmware
        self._port = port

    def run(self):
        try:
            from esp_flasher.__main__ import run_esp_flasher

            run_esp_flasher(self._port, self._firmware)
        except Exception as e:
            print("Unexpected error: {}".format(e))
            raise


class ChipInfoThread(QThread):
    mac_address_signal = pyqtSignal(str)  # Signal to send MAC address to MainWindow
    error_signal = pyqtSignal(str)  # Signal for error handling

    def __init__(self, port):
        super().__init__()
        self.daemon = True
        self._port = port

    def run(self):
        try:
            from esp_flasher.__main__ import dump_info, detect_chip, read_chip_info

            dump_info(self._port)
            chip = detect_chip(self._port)
            info = read_chip_info(chip)
            chip._port.close()
            self.mac_address = info.mac  # Store MAC address
            self.mac_address_signal.emit(self.mac_address)  # Emit MAC address
        except Exception as e:
            self.error_signal.emit(
                f"Error: {str(e)}"
            )  # Emit error message instead of crashing


class LogThread(threading.Thread):
    def __init__(self, port, stop=False):
        threading.Thread.__init__(self)
        self.daemon = True
        self._port = port
        self._stop = stop

    def run(self):
        try:
            from esp_flasher.__main__ import show_logs, stop_logs

            if self._stop == True:
                stop_logs()
            else:
                show_logs(self._port)
        except Exception as e:
            print("Unexpected error: {}".format(e))
            raise


class PrintingThread(QThread):
    success_signal = pyqtSignal(str)  # Signal for success messages
    error_signal = pyqtSignal(str)  # Signal for error messages

    def __init__(self, printer_port, device_name):
        super().__init__()
        self._device_name = device_name
        self._printer_port = printer_port

    def run(self):
        """Runs the print job safely and emits signals based on the outcome."""
        try:
            from esp_flasher.printer import print_message

            if not self._device_name:
                self.error_signal.emit(
                    "Error: Device name is missing. Please register the device first."
                )
                return

            print_message(self._printer_port, self._device_name)
            self.success_signal.emit(f"Printed successfully: {self._device_name}")

        except Exception as e:
            self.error_signal.emit(f"Printing Error: {str(e)}")


class RegisterThread(QThread):
    device_name_signal = pyqtSignal(str)  # Signal for successful registration
    error_signal = pyqtSignal(str)  # Signal for error handling

    def __init__(self, api_endpoint, api_key, api_secret, mac_address):
        super().__init__()
        self._api_endpoint = api_endpoint
        self._api_key = api_key
        self._api_secret = api_secret
        self._mac = mac_address

    def run(self):
        """Publishes MAC address and handles API response."""
        try:
            from esp_flasher.backend import publish_mac_address

            device_name, error_message = publish_mac_address(
                self._api_endpoint, self._api_key, self._api_secret, self._mac
            )

            if device_name:
                self.device_name_signal.emit(
                    device_name
                )  # Emit device name if successful
            else:
                self.error_signal.emit(error_message)  # Emit error if request failed

        except Exception as e:
            self.error_signal.emit(f"Unexpected error: {e}")  # Handle unexpected errors


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._firmware = None
        self._chip_port = None
        self._printer_port = None
        # Variables to store backend connection values
        self._api_endpoint = ""
        self._api_key = ""
        self._api_secret = ""
        self._mac_address = None  # Store MAC address
        self._device_name = ""

        self.init_ui()
        sys.stdout = RedirectText(self.console)  # Redirect stdout to console

    def init_ui(self):
        self.setWindowTitle(f"ESP32-GUI-Flasher with Printer Support {__version__}")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icon.ico"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        vbox = QVBoxLayout()

        port_group_box = QGroupBox("Port Configuration")
        port_layout = QGridLayout()
        port_label = QLabel("Select Chip Port:")
        self.port_combobox = QComboBox()
        self.port_combobox.currentIndexChanged.connect(self.select_port)
        printer_port_label = QLabel("Select Printer Port:")
        self.printer_port_combobox = QComboBox()
        self.printer_port_combobox.currentIndexChanged.connect(self.select_printer_port)
        self.reload_ports()

        reload_button = QPushButton("Reload")
        reload_button.clicked.connect(self.reload_ports)

        port_layout.addWidget(port_label, 0, 0)
        port_layout.addWidget(self.port_combobox, 0, 1)
        port_layout.addWidget(reload_button, 0, 2)
        port_layout.addWidget(printer_port_label, 1, 0)
        port_layout.addWidget(self.printer_port_combobox, 1, 1)
        port_group_box.setLayout(port_layout)

        # Create Group Box
        backend_connection_group_box = QGroupBox("Backend Connection")
        backend_connection_layout = QVBoxLayout()

        # Create Labels and LineEdits
        self.fields = {
            "API Endpoint": "_api_endpoint",
            "API Key": "_api_key",
            "API Secret": "_api_secret",
        }
        self.line_edits = {}

        for label_text, var_name in self.fields.items():
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            line_edit = QLineEdit()
            line_edit.textChanged.connect(
                lambda text, v=var_name: self.on_text_changed(text, v)
            )
            self.line_edits[var_name] = line_edit

            row_layout.addWidget(label)
            row_layout.addWidget(line_edit)

            backend_connection_layout.addLayout(row_layout)

        backend_connection_group_box.setLayout(backend_connection_layout)

        chip_info_group_box = QGroupBox("Chip Info")
        chip_info_layout = QHBoxLayout()
        self.get_device_info_button = QPushButton("Get Device Info")
        self.get_device_info_button.clicked.connect(self.get_device_info)
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.register)
        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.print)
        chip_info_layout.addWidget(self.get_device_info_button)
        chip_info_layout.addWidget(self.register_button)
        chip_info_layout.addWidget(self.print_button)
        chip_info_group_box.setLayout(chip_info_layout)

        firmware_group_box = QGroupBox("Firmware")
        firmware_layout = QGridLayout()
        firmware_label = QLabel("Select Firmware:")
        self.firmware_button = QPushButton("Browse")
        self.firmware_button.clicked.connect(self.pick_file)
        firmware_layout.addWidget(firmware_label, 0, 0)
        firmware_layout.addWidget(self.firmware_button, 0, 1)
        firmware_group_box.setLayout(firmware_layout)

        actions_group_box = QGroupBox("Actions")
        actions_layout = QHBoxLayout()
        self.flash_button = QPushButton("Flash ESP")
        self.flash_button.clicked.connect(self.flash_esp)
        self.logs_button = QPushButton("View Logs")
        self.logs_button.clicked.connect(self.view_logs)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.stop_logs)
        actions_layout.addWidget(self.flash_button)
        actions_layout.addWidget(self.logs_button)
        actions_layout.addWidget(self.clear_button)
        actions_group_box.setLayout(actions_layout)

        console_group_box = QGroupBox("Console")
        console_layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        console_layout.addWidget(self.console)
        console_group_box.setLayout(console_layout)

        vbox.addWidget(port_group_box)
        vbox.addWidget(backend_connection_group_box)
        vbox.addWidget(chip_info_group_box)
        vbox.addWidget(firmware_group_box)
        vbox.addWidget(actions_group_box)
        vbox.addWidget(console_group_box)

        central_widget.setLayout(vbox)

    def reload_ports(self):
        self.port_combobox.clear()
        self.printer_port_combobox.clear()

        ports = list_serial_ports()
        if ports:
            self.port_combobox.addItems(ports)
            self.printer_port_combobox.addItems(ports)
        else:
            self.port_combobox.addItem("")

    def select_port(self, index):
        self._chip_port = self.port_combobox.itemText(index)

    def select_printer_port(self, index):
        self._printer_port = self.printer_port_combobox.itemText(index)

    def pick_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Firmware File",
            "",
            "ZIP Files (*.zip);;All Files (*)",
            options=options,
        )
        if file_name:
            self._firmware = file_name
            self.firmware_button.setText(file_name)

    def flash_esp(self):
        self.console.clear()
        if self._firmware and self._chip_port:
            worker = FlashingThread(self._firmware, self._chip_port)
            worker.start()

    def view_logs(self):
        self.console.clear()
        if self._chip_port:
            worker = LogThread(self._chip_port)
            worker.start()

    def stop_logs(self):
        self.console.clear()
        if self._chip_port:
            worker = LogThread(self._chip_port, stop=True)
            worker.start()
        self.console.clear()

    def get_device_info(self):
        self.console.clear()
        if self._chip_port:
            self.chip_info_thread = ChipInfoThread(self._chip_port)
            self.chip_info_thread.mac_address_signal.connect(self.update_mac_address)
            self.chip_info_thread.error_signal.connect(
                self.show_message
            )  # Handle errors
            self.chip_info_thread.start()

    def update_mac_address(self, mac):
        self._mac_address = mac  # Store MAC address

    def show_message(self, error_message):
        """Displays errors instead of crashing."""
        print(error_message)  # Show error on UI

    def register(self):
        self.console.clear()
        if (
            self._api_endpoint
            and self._api_key
            and self._api_secret
            and self._mac_address
        ):
            """Starts device registration."""
            self.register_thread = RegisterThread(
                self._api_endpoint, self._api_key, self._api_secret, self._mac_address
            )
            self.register_thread.device_name_signal.connect(self.update_device_name)
            self.register_thread.error_signal.connect(self.show_message)
            self.register_thread.start()
        else:
            if not self._mac_address:
                print("No MAC address, first click Get Device Info!")
            else:
                print(
                    f"One or more of the following fields are empty: API Endpoint, API Key or API Secret."
                )

    def update_device_name(self, device_name):
        """Updates UI when registration is successful."""
        self._device_name = device_name
        print(f"Device Name: {device_name}")

    def print(self):
        self.console.clear()
        if self._chip_port:
            """Starts the printing process using `PrintingThread`."""
            if not self._device_name:
                print("Error: Device name not obtained, first Register the device.")
                return

            self.print_thread = PrintingThread(self._printer_port, self._device_name)
            self.print_thread.success_signal.connect(self.show_message)
            self.print_thread.error_signal.connect(self.show_message)
            self.print_thread.start()

    def on_text_changed(self, text, field_name):
        setattr(self, field_name, text)
        print(f"{field_name} updated: {text}")


def main():

    os_name = platform.system()
    if os_name == "Darwin":
        os.environ["QT_QPA_PLATFORM"] = "cocoa"
    elif os_name == "Linux":
        distro_name = distro.id().lower()
        if "ubuntu" in distro_name or "debian" in distro_name:
            os.environ["QT_QPA_PLATFORM"] = "wayland"
        else:
            os.environ["QT_QPA_PLATFORM"] = "xcb"
    elif os_name == "Windows":
        os.environ["QT_QPA_PLATFORM"] = "windows"
    else:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    app = QApplication(sys.argv)

    app.setStyle("Fusion")
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
    app.setPalette(palette)

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

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
)
from PyQt5.QtGui import QColor, QTextCursor, QPalette, QColor, QIcon
from PyQt5.QtCore import pyqtSignal, QObject

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


class ChipInfoThread(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.daemon = True
        self._port = port

    def run(self):
        try:
            from esp_flasher.__main__ import dump_info

            dump_info(self._port)
        except Exception as e:
            print("Unexpected error: {}".format(e))
            raise


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


class PrintingThread(threading.Thread):
    def __init__(self, chip_port, printer_port):
        threading.Thread.__init__(self)
        self.daemon = True
        self._chip_port = chip_port
        self._printer_port = printer_port

    def run(self):
        try:
            from esp_flasher.printer import print_message
            from esp_flasher.common import detect_chip, read_chip_info

            chip = detect_chip(self._chip_port)
            info = read_chip_info(chip)
            chip._port.close()

            # Print on thermal printer
            print_message(self._printer_port, f"Device Name: GB_{info.mac}")
        except Exception as e:
            print("Unexpected error: {}".format(e))
            raise


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._firmware = None
        self._chip_port = None
        self._printer_port = None

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

        chip_info_group_box = QGroupBox("Chip Info")
        chip_info_layout = QHBoxLayout()
        self.get_device_info_button = QPushButton("Get Device Info")
        self.get_device_info_button.clicked.connect(self.get_device_info)
        self.print_button = QPushButton("Print")
        self.print_button.clicked.connect(self.print)
        chip_info_layout.addWidget(self.get_device_info_button)
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
        vbox.addWidget(firmware_group_box)
        vbox.addWidget(chip_info_group_box)
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
            worker = ChipInfoThread(self._chip_port)
            worker.start()

    def print(self):
        self.console.clear()
        if self._chip_port:
            worker = PrintingThread(self._chip_port, self._printer_port)
            worker.start()


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

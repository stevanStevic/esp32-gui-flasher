from PyQt5.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
)
from esp_flasher.helpers.printer_utils import list_available_printers


class PrinterConfig(QGroupBox):
    def __init__(self, parent):
        super().__init__("Printer Setup")
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Printer selection
        printer_layout = QHBoxLayout()
        printer_label = QLabel("Select Printer:")
        self.printer_combobox = QComboBox()
        self.printer_combobox.currentIndexChanged.connect(self.select_port)
        self.refresh_printer_list()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_printer_list)

        printer_layout.addWidget(printer_label)
        printer_layout.addWidget(self.printer_combobox)
        printer_layout.addWidget(refresh_button)

        layout.addLayout(printer_layout)
        self.setLayout(layout)

    def refresh_printer_list(self):
        """Refreshes available printers"""
        self.printer_combobox.clear()
        printers = list_available_printers()
        if printers:
            self.printer_combobox.addItems(printers)
        else:
            self.printer_combobox.addItem("No printers found")

    def select_port(self, index):
        self.parent._printer_port = self.printer_combobox.itemText(index)

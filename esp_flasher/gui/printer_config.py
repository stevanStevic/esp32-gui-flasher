import logging
from PyQt5.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QSpinBox,
    QLineEdit,
)
from esp_flasher.helpers.printer_utils import list_available_printers
from esp_flasher.threads.printing_thread import PrintingThread


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

        # Label width configuration
        width_layout = QHBoxLayout()
        width_label = QLabel("Label Width (mm):")
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(20, 100)  # Define reasonable width limits
        self.width_spinbox.setValue(62)  # Default width for QL-600

        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_spinbox)

        # Font size configuration
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("Font Size (pt):")
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(6, 72)  # Define reasonable font size limits
        self.font_size_spinbox.setValue(20)  # Default font size

        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_spinbox)

        # Text rotation configuration
        rotation_layout = QHBoxLayout()
        rotation_label = QLabel("Text Rotation (°):")
        self.rotation_spinbox = QSpinBox()
        self.rotation_spinbox.setRange(0, 360)
        self.rotation_spinbox.setSingleStep(90)  # Typical rotations
        self.rotation_spinbox.setValue(270)  # Default rotation

        rotation_layout.addWidget(rotation_label)
        rotation_layout.addWidget(self.rotation_spinbox)

        # Offset configuration
        offset_layout = QHBoxLayout()
        x_offset_label = QLabel("X Offset:")
        self.x_offset_spinbox = QSpinBox()
        self.x_offset_spinbox.setRange(0, 1000)
        self.x_offset_spinbox.setValue(100)

        y_offset_label = QLabel("Y Offset:")
        self.y_offset_spinbox = QSpinBox()
        self.y_offset_spinbox.setRange(0, 1000)
        self.y_offset_spinbox.setValue(100)

        offset_layout.addWidget(x_offset_label)
        offset_layout.addWidget(self.x_offset_spinbox)
        offset_layout.addWidget(y_offset_label)
        offset_layout.addWidget(self.y_offset_spinbox)

        # Test Print Button
        test_print_layout = QHBoxLayout()
        custom_print_label = QLabel("Print Text:")
        self.custom_print_input = QLineEdit()
        self.custom_print_input.setText("Test Print - ESP Flasher")

        test_print_button = QPushButton("Test Print")
        test_print_button.clicked.connect(self.test_print)

        test_print_layout.addWidget(custom_print_label)
        test_print_layout.addWidget(self.custom_print_input)
        test_print_layout.addWidget(test_print_button)

        layout.addLayout(printer_layout)
        layout.addLayout(width_layout)
        layout.addLayout(font_size_layout)
        layout.addLayout(rotation_layout)
        layout.addLayout(offset_layout)
        layout.addLayout(test_print_layout)
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

    def test_print(self):
        """Sends a test print job to the selected printer."""
        printer_name = self.printer_combobox.currentText()
        if not printer_name or printer_name == "No printers found":
            logging.error("No printer selected!")
            return

        label_width = self.width_spinbox.value()
        font_size = self.font_size_spinbox.value()
        text_rotation = self.rotation_spinbox.value()
        x_offset = self.x_offset_spinbox.value()
        y_offset = self.y_offset_spinbox.value()

        self.parent.console.clear()

        self.print_thread = PrintingThread(
            printer_name,
            self.custom_print_input.text(),
            label_width,
            x_offset,
            y_offset,
            text_rotation,
            font_size,
        )
        self.print_thread.start()

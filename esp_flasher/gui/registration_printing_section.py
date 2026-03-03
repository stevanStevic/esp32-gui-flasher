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
from esp_flasher.threads.register_thread import RegisterThread


class RegistrationPrintingSection(QGroupBox):
    """Combined section for Backend Connection, Printer Setup, Register and Print."""

    def __init__(self, parent):
        super().__init__("Device Registration and Printing")
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Backend Connection ---
        backend_label = QLabel("Backend Connection")
        backend_label.setStyleSheet("font-weight: bold; color: white; font-size: 13px; margin-top: 6px;")
        layout.addWidget(backend_label)

        self.fields = {
            "API Endpoint": "_api_endpoint",
            "API Key": "_api_key",
            "API Secret": "_api_secret",
        }
        self.line_edits = {}

        for label_text, var_name in self.fields.items():
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setFixedWidth(90)
            line_edit = QLineEdit()

            if var_name in ["_api_key", "_api_secret"]:
                line_edit.setEchoMode(QLineEdit.Password)

            line_edit.textChanged.connect(
                lambda text, v=var_name: self._on_text_changed(text, v)
            )
            self.line_edits[var_name] = line_edit

            row_layout.addWidget(label)
            row_layout.addWidget(line_edit, 1)
            layout.addLayout(row_layout)

        # --- Printer Setup ---
        printer_label = QLabel("Printer Setup")
        printer_label.setStyleSheet("font-weight: bold; color: white; font-size: 13px; margin-top: 6px;")
        layout.addWidget(printer_label)

        # Printer selection
        printer_layout = QHBoxLayout()
        printer_select_label = QLabel("Select Printer:")
        self.printer_combobox = QComboBox()
        self.printer_combobox.currentIndexChanged.connect(self._select_printer)
        self.refresh_printer_list()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_printer_list)

        printer_layout.addWidget(printer_select_label)
        printer_layout.addWidget(self.printer_combobox)
        printer_layout.addWidget(refresh_button)
        layout.addLayout(printer_layout)

        # Label width
        width_layout = QHBoxLayout()
        width_label = QLabel("Label Width (mm):")
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(20, 100)
        self.width_spinbox.setValue(62)
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_spinbox)
        layout.addLayout(width_layout)

        # Font size
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("Font Size (pt):")
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(6, 72)
        self.font_size_spinbox.setValue(20)
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_spinbox)
        layout.addLayout(font_size_layout)

        # Text rotation
        rotation_layout = QHBoxLayout()
        rotation_label = QLabel("Text Rotation (°):")
        self.rotation_spinbox = QSpinBox()
        self.rotation_spinbox.setRange(0, 360)
        self.rotation_spinbox.setSingleStep(90)
        self.rotation_spinbox.setValue(270)
        rotation_layout.addWidget(rotation_label)
        rotation_layout.addWidget(self.rotation_spinbox)
        layout.addLayout(rotation_layout)

        # Offsets
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
        layout.addLayout(offset_layout)

        # Test Print
        test_print_layout = QHBoxLayout()
        custom_print_label = QLabel("Print Text:")
        custom_print_label.setFixedWidth(90)
        self.custom_print_input = QLineEdit()
        self.custom_print_input.setText("Test Print - ESP Flasher")
        test_print_button = QPushButton("Test Print")
        test_print_button.clicked.connect(self.test_print)
        test_print_layout.addWidget(custom_print_label)
        test_print_layout.addWidget(self.custom_print_input, 1)
        test_print_layout.addWidget(test_print_button)
        layout.addLayout(test_print_layout)

        # --- Register & Print Buttons ---
        actions_label = QLabel("Device Actions")
        actions_label.setStyleSheet("font-weight: bold; color: white; font-size: 13px; margin-top: 6px;")
        layout.addWidget(actions_label)

        actions_layout = QHBoxLayout()
        self.register_button = QPushButton("Register Device (2)")
        self.register_button.clicked.connect(self.register)
        self.print_button = QPushButton("Print (3)")
        self.print_button.clicked.connect(self.print_device)
        actions_layout.addWidget(self.register_button)
        actions_layout.addWidget(self.print_button)
        layout.addLayout(actions_layout)

        self.setLayout(layout)

    # --- Backend handlers ---

    def _on_text_changed(self, text, field_name):
        setattr(self.parent, field_name, text)

    # --- Printer handlers ---

    def refresh_printer_list(self):
        self.printer_combobox.clear()
        printers = list_available_printers()
        if printers:
            self.printer_combobox.addItems(printers)
        else:
            self.printer_combobox.addItem("No printers found")

    def _select_printer(self, index):
        self.parent._printer_port = self.printer_combobox.itemText(index)

    def test_print(self):
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

    # --- Register & Print handlers ---

    def register(self):
        self.parent.console.clear()

        if (
            not self.parent._api_endpoint
            or not self.parent._api_key
            or not self.parent._api_secret
        ):
            logging.error("API endpoint and/or credentials are missing!")
            return

        if not self.parent._mac_address:
            logging.error("No MAC address found! Click 'Get Device Info' first.")
            return

        self.parent.console.clear()
        self.register_thread = RegisterThread(
            self.parent._api_endpoint,
            self.parent._api_key,
            self.parent._api_secret,
            self.parent._mac_address,
        )
        self.register_thread.device_name_signal.connect(self._update_device_name)
        self.register_thread.start()

    def _update_device_name(self, device_name):
        self.parent._device_name = device_name
        logging.info(f"Device Registered: {device_name}")

    def print_device(self):
        self.parent.console.clear()

        if not self.parent._printer_port:
            logging.error("No printer port selected!")
            return

        if not self.parent._device_name:
            logging.error("Device name not obtained, first Register the device.")
            return

        label_width = self.width_spinbox.value()
        text_rotation = self.rotation_spinbox.value()
        x_offset = self.x_offset_spinbox.value()
        y_offset = self.y_offset_spinbox.value()
        font_size = self.font_size_spinbox.value()

        self.print_thread = PrintingThread(
            self.parent._printer_port,
            self.parent._device_name,
            label_width,
            x_offset,
            y_offset,
            text_rotation,
            font_size,
        )
        self.print_thread.start()

import logging
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, QThread
from esp_flasher.threads.chip_info_thread import ChipInfoThread
from esp_flasher.threads.register_thread import RegisterThread
from esp_flasher.threads.printing_thread import PrintingThread


class ChipInfoSection(QGroupBox):
    def __init__(self, parent):
        super().__init__("Chip Info")
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        self.get_device_info_button = QPushButton("Get Device Info (1)")
        self.get_device_info_button.clicked.connect(self.get_device_info)

        self.register_button = QPushButton("Register Device (2)")
        self.register_button.clicked.connect(self.register)

        self.print_button = QPushButton("Print (3)")
        self.print_button.clicked.connect(self.print_device)

        layout.addWidget(self.get_device_info_button)
        layout.addWidget(self.register_button)
        layout.addWidget(self.print_button)

        self.setLayout(layout)

    def get_device_info(self):
        if self.parent._chip_port:
            self.parent.console.clear()
            self.chip_info_thread = ChipInfoThread(self.parent._chip_port)
            self.chip_info_thread.mac_address_signal.connect(self.update_mac_address)
            self.chip_info_thread.start()
        else:
            logging.error("Device port is missing!")

    def update_mac_address(self, mac):
        self.parent._mac_address = mac

    def register(self):
        self.parent.console.clear()

        """Starts device registration."""
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
        self.register_thread.device_name_signal.connect(self.update_device_name)
        self.register_thread.start()

    def update_device_name(self, device_name):
        """Updates the stored device name and UI."""
        self.parent._device_name = device_name
        logging.info(f"Device Registered: {device_name}")

    def print_device(self):
        self.parent.console.clear()

        """Starts the printing process."""
        if not self.parent._printer_port:
            logging.error("No printer port selected!")
            return

        if not self.parent._device_name:
            logging.error("Device name not obtained, first Register the device.")
            return

        label_width = self.parent.printer_config.width_spinbox.value()
        text_rotation = self.parent.printer_config.rotation_spinbox.value()
        x_offset = self.parent.printer_config.x_offset_spinbox.value()
        y_offset = self.parent.printer_config.y_offset_spinbox.value()
        font_size = self.parent.printer_config.font_size_spinbox.value()

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

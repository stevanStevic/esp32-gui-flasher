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

        self.get_device_info_button = QPushButton("Get Device Info")
        self.get_device_info_button.clicked.connect(self.get_device_info)

        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.register)

        self.print_button = QPushButton("Print")
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
            self.chip_info_thread.error_signal.connect(self.parent.show_message)
            self.chip_info_thread.start()

    def update_mac_address(self, mac):
        self.parent._mac_address = mac

    def register(self):
        """Starts device registration."""
        if (
            not self.parent._api_endpoint
            or not self.parent._api_key
            or not self.parent._api_secret
        ):
            self.parent.show_message("Error: API credentials are missing!")
            return

        if not self.parent._mac_address:
            self.parent.show_message(
                "Error: No MAC address found! Click 'Get Device Info' first."
            )
            return

        self.register_thread = RegisterThread(
            self.parent._api_endpoint,
            self.parent._api_key,
            self.parent._api_secret,
            self.parent._mac_address,
        )
        self.register_thread.device_name_signal.connect(self.update_device_name)
        self.register_thread.error_signal.connect(self.parent.show_message)
        self.register_thread.start()

    def update_device_name(self, device_name):
        """Updates the stored device name and UI."""
        self.parent._device_name = device_name
        self.parent.show_message(f"Device Registered: {device_name}")

    def print_device(self):
        """Starts the printing process."""
        if not self.parent._printer_port:
            self.parent.show_message("Error: No printer port selected!")
            return

        if not self.parent._device_name:
            self.parent.show_message(
                "Error: Device name not obtained, first Register the device."
            )
            return

        self.print_thread = PrintingThread(
            self.parent._printer_port, self.parent._device_name
        )
        self.print_thread.success_signal.connect(self.parent.show_message)
        self.print_thread.error_signal.connect(self.parent.show_message)
        self.print_thread.start()

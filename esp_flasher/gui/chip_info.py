import logging
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, QThread
from esp_flasher.threads.chip_info_thread import ChipInfoThread


class ChipInfoSection(QGroupBox):
    def __init__(self, parent):
        super().__init__("Chip Info")
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        self.get_device_info_button = QPushButton("Get Device Info (1)")
        self.get_device_info_button.clicked.connect(self.get_device_info)

        layout.addWidget(self.get_device_info_button)

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

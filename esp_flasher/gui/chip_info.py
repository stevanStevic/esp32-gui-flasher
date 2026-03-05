import logging
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton
from esp_flasher.gui.threads.chip_info_thread import ChipInfoThread


class ChipInfoSection(QGroupBox):
    def __init__(self, state):
        super().__init__("Chip Info")
        self.state = state
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        self.get_device_info_button = QPushButton("Get Device Info")
        self.get_device_info_button.clicked.connect(self.get_device_info)

        layout.addWidget(self.get_device_info_button)

        self.setLayout(layout)

    def get_device_info(self):
        if self.state.chip_port:
            self.state.console.clear()
            self.chip_info_thread = ChipInfoThread(self.state.chip_port)
            self.chip_info_thread.mac_address_signal.connect(self.update_mac_address)
            self.chip_info_thread.start()
        else:
            logging.error("Device port is missing!")

    def update_mac_address(self, mac):
        self.state.mac_address = mac

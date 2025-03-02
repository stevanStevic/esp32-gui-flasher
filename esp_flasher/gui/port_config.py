from PyQt5.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
)
from esp_flasher.helpers.serial_utils import list_serial_ports


class PortConfig(QGroupBox):
    def __init__(self, parent):
        super().__init__("Chip Port Configuration")
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Chip Port selection
        chip_port_layout = QHBoxLayout()
        chip_port_label = QLabel("Select Chip Port:")
        self.chip_port_combobox = QComboBox()
        self.chip_port_combobox.currentIndexChanged.connect(self.select_port)
        self.refresh_chip_ports()

        reload_button = QPushButton("Refresh")
        reload_button.clicked.connect(self.refresh_chip_ports)

        chip_port_layout.addWidget(chip_port_label)
        chip_port_layout.addWidget(self.chip_port_combobox)
        chip_port_layout.addWidget(reload_button)

        layout.addLayout(chip_port_layout)
        self.setLayout(layout)

    def refresh_chip_ports(self):
        """Refreshes available serial ports for the chip."""
        self.chip_port_combobox.clear()
        ports = list_serial_ports()
        if ports:
            self.chip_port_combobox.addItems(ports)
        else:
            self.chip_port_combobox.addItem("No serial ports found")

    def select_port(self, index):
        self.parent._chip_port = self.chip_port_combobox.itemText(index)

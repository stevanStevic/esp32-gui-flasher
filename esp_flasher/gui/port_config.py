from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QComboBox, QPushButton
from esp_flasher.helpers.serial_utils import list_serial_ports


class PortConfig(QGroupBox):
    def __init__(self, parent):
        super().__init__("Port Configuration")
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        port_label = QLabel("Select Chip Port:")
        self.port_combobox = QComboBox()
        self.port_combobox.currentIndexChanged.connect(self.select_port)

        printer_port_label = QLabel("Select Printer Port:")
        self.printer_port_combobox = QComboBox()
        self.printer_port_combobox.currentIndexChanged.connect(self.select_printer_port)

        self.reload_ports()

        reload_button = QPushButton("Reload")
        reload_button.clicked.connect(self.reload_ports)

        layout.addWidget(port_label, 0, 0)
        layout.addWidget(self.port_combobox, 0, 1)
        layout.addWidget(reload_button, 0, 2)
        layout.addWidget(printer_port_label, 1, 0)
        layout.addWidget(self.printer_port_combobox, 1, 1)

        self.setLayout(layout)

    def reload_ports(self):
        self.port_combobox.clear()
        self.printer_port_combobox.clear()

        ports = list_serial_ports()
        if ports:
            self.port_combobox.addItems(ports)
            self.printer_port_combobox.addItems(ports)
        else:
            self.port_combobox.addItem("No Ports Found")

    def select_port(self, index):
        self.parent._chip_port = self.port_combobox.itemText(index)

    def select_printer_port(self, index):
        self.parent._printer_port = self.printer_port_combobox.itemText(index)

from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QPushButton, QFileDialog


class FirmwareSection(QGroupBox):
    def __init__(self, parent):
        super().__init__("Firmware")
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        firmware_label = QLabel("Select Firmware:")
        self.firmware_button = QPushButton("Browse")
        self.firmware_button.clicked.connect(self.pick_file)

        layout.addWidget(firmware_label, 0, 0)
        layout.addWidget(self.firmware_button, 0, 1)

        self.setLayout(layout)

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
            self.parent._firmware = file_name
            self.firmware_button.setText(file_name)

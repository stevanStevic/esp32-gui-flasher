from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit


class BackendConfig(QGroupBox):
    def __init__(self, parent):
        super().__init__("Backend Connection")
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.fields = {
            "API Endpoint": "_api_endpoint",
            "API Key": "_api_key",
            "API Secret": "_api_secret",
        }
        self.line_edits = {}

        for label_text, var_name in self.fields.items():
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            line_edit = QLineEdit()
            line_edit.textChanged.connect(
                lambda text, v=var_name: self.on_text_changed(text, v)
            )
            self.line_edits[var_name] = line_edit

            row_layout.addWidget(label)
            row_layout.addWidget(line_edit)
            layout.addLayout(row_layout)

        self.setLayout(layout)

    def on_text_changed(self, text, field_name):
        setattr(self.parent, field_name, text)

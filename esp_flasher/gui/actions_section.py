from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton
from esp_flasher.threads.log_thread import LogThread
from esp_flasher.threads.flashing_thread import FlashingThread


class ActionsSection(QGroupBox):
    def __init__(self, parent):
        super().__init__("Actions")
        self.parent = parent
        self.flashing_thread = None  # Store the thread reference
        self.log_thread = None  # Keep track of LogThread instance
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        self.flash_button = QPushButton("Flash ESP")
        self.flash_button.clicked.connect(self.flash_esp)

        self.logs_button = QPushButton("View Logs")
        self.logs_button.clicked.connect(self.view_logs)

        self.clear_button = QPushButton("Stop Logs")
        self.clear_button.clicked.connect(self.stop_logs)

        layout.addWidget(self.flash_button)
        layout.addWidget(self.logs_button)
        layout.addWidget(self.clear_button)

        self.setLayout(layout)

    def flash_esp(self):
        """Starts flashing process in a thread and ensures no duplicate instances."""
        if not self.parent._firmware or not self.parent._chip_port:
            self.parent.show_message("Error: Please select firmware and a chip port.")
            return

        if self.flashing_thread and self.flashing_thread.isRunning():
            self.parent.show_message("Flashing already in progress.")
            return

        self.parent.console.clear()
        self.parent.show_message("Starting flashing process...")

        self.flashing_thread = FlashingThread(
            self.parent._firmware, self.parent._chip_port
        )
        self.flashing_thread.success_signal.connect(self.parent.show_message)
        self.flashing_thread.error_signal.connect(self.parent.show_message)
        self.flashing_thread.finished_signal.connect(self.handle_flash_completion)
        self.flashing_thread.start()

    def handle_flash_completion(self, success):
        """Starts logging only if flashing was successful."""
        self.cleanup_flashing_thread()

    def cleanup_flashing_thread(self):
        """Cleans up the flashing thread after completion."""
        self.flashing_thread = None

    def view_logs(self):
        """Starts log viewing inside LogThread."""
        if not self.parent._chip_port:
            self.parent.show_message("Error: No chip port selected!")
            return

        self.parent.console.clear()
        self.parent.show_message("Starting log monitoring...")

        if self.log_thread is None:
            self.log_thread = LogThread(self.parent._chip_port)
            self.log_thread.log_signal.connect(self.parent.show_colored_message)
            self.log_thread.error_signal.connect(self.parent.show_message)

        self.log_thread.start()

    def stop_logs(self):
        """Stops log monitoring using LogThread."""
        if self.log_thread:
            self.log_thread.stop_logging()
            self.log_thread = None

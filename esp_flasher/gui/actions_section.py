import logging
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton
from esp_flasher.threads.log_thread import LogThread
from esp_flasher.threads.flashing_thread import FlashingThread
from esp_flasher.threads.test_thread import TestThread
from esp_flasher.helpers.utils import (
    get_device_dir,
    get_flash_log_path,
    get_testing_log_path,
)


class ActionsSection(QGroupBox):
    def __init__(self, parent):
        super().__init__("Actions")
        self.parent = parent
        self.flashing_thread = None  # Store the thread reference
        self.log_thread = None  # Keep track of LogThread instance
        self.test_thread = None  # Will be created when test starts
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        self.flash_button = QPushButton("Flash ESP (4)")
        self.flash_button.clicked.connect(self.flash_esp)

        self.logs_button = QPushButton("View Logs")
        self.logs_button.clicked.connect(self.view_logs)

        self.clear_button = QPushButton("Stop Logs")
        self.clear_button.clicked.connect(self.stop_logs)

        self.test_button = QPushButton("Test Device")
        self.test_button.clicked.connect(self.manual_test_device)

        layout.addWidget(self.flash_button)
        layout.addWidget(self.logs_button)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.test_button)
        self.setLayout(layout)

    def flash_esp(self):
        if not self.parent._firmware or not self.parent._chip_port:
            logging.error("Please select firmware and a chip port.")
            return
        if self.flashing_thread and self.flashing_thread.isRunning():
            logging.warning("Flashing already in progress.")
            return
        self.parent.console.clear()
        logging.info("Starting flashing process...")
        # Generate device dir and log file
        device_dir = get_device_dir(
            getattr(self.parent, "_device_name", None),
            getattr(self.parent, "_mac_address", None),
        )
        flash_log_path = get_flash_log_path(device_dir)
        self.parent.set_log_file(flash_log_path)
        self.flashing_thread = FlashingThread(
            self.parent._firmware, self.parent._chip_port
        )

        self.flashing_thread.finished_signal.connect(self.handle_flash_completion)
        self.flashing_thread.start()

    def handle_flash_completion(self, success):
        self.cleanup_flashing_thread()
        self.parent.close_log_file()

        if success:
            self.parent.test_module.increment_flash_count()
            if self.parent.test_module.should_run_test():
                self.start_test_thread()
            else:
                self.parent.show_success_popup("Flashing completed successfully!")

    def start_test_thread(self):
        # Set up testing log file
        device_dir = get_device_dir(
            getattr(self.parent, "_device_name", None),
            getattr(self.parent, "_mac_address", None),
        )
        test_log_path = get_testing_log_path(device_dir)
        self.parent.set_log_file(test_log_path)

        # Create a new TestThread with the latest model
        self.test_thread = TestThread(self.parent.test_module)
        self.test_thread.test_timeout_signal.connect(self.parent.show_error_popup)
        self.test_thread.test_success_signal.connect(self.parent.show_success_popup)
        self.test_thread.test_started_signal.connect(self.parent.show_testing_popup)
        self.test_thread.test_stopped_signal.connect(self.handle_test_end)
        self.test_thread.start_test()
        self.view_logs()

    def manual_test_device(self):
        self.start_test_thread()

    def cleanup_flashing_thread(self):
        """Cleans up the flashing thread after completion."""
        self.flashing_thread = None

    def view_logs(self):
        """Starts log viewing inside LogThread."""
        if not self.parent._chip_port:
            logging.error("No chip port selected!")
            return

        self.parent.console.clear()
        logging.info("Starting log monitoring...")

        if self.log_thread is None:
            self.log_thread = LogThread(self.parent._chip_port)
            # Connect log signal to test_thread if exists
            if self.test_thread:
                self.log_thread.log_signal.connect(self.test_thread.process_log_line)
            self.log_thread.error_signal.connect(logging.error)

        self.log_thread.start()

    def stop_logs(self):
        """Stops log monitoring using LogThread."""
        if self.log_thread:
            self.log_thread.stop_logging()
            self.log_thread = None

    def handle_test_end(self):
        """Handles the end of the test."""
        # Disconnect log_signal from test_thread if connected
        if self.log_thread and self.test_thread:
            try:
                self.log_thread.log_signal.disconnect(self.test_thread.process_log_line)
            except (TypeError, RuntimeError):
                pass  # Already disconnected or thread deleted
        self.parent.close_testing_popup()
        self.stop_logs()
        self.parent.close_log_file()
        # self.test_thread = None

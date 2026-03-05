import logging
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton
from esp_flasher.gui.threads.log_thread import LogThread
from esp_flasher.gui.threads.flashing_thread import FlashingThread
from esp_flasher.gui.threads.test_thread import TestThread
from esp_flasher.helpers.utils import (
    get_device_dir,
    get_flash_log_path,
    get_testing_log_path,
)


class ActionsSection(QGroupBox):
    def __init__(self, state):
        super().__init__("Actions")
        self.state = state
        self.flashing_thread = None  # Store the thread reference
        self.log_thread = None  # Keep track of LogThread instance
        self.test_thread = None  # Will be created when test starts
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        self.logs_button = QPushButton("View Logs")
        self.logs_button.clicked.connect(self.view_logs)

        self.clear_button = QPushButton("Stop Logs")
        self.clear_button.clicked.connect(self.stop_logs)

        self.test_button = QPushButton("Test Device")
        self.test_button.clicked.connect(self.manual_test_device)

        layout.addWidget(self.logs_button)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.test_button)
        self.setLayout(layout)

    def flash_esp(self):
        if not self.state.firmware or not self.state.chip_port:
            logging.error("Please select firmware and a chip port.")
            return
        if self.flashing_thread and self.flashing_thread.isRunning():
            logging.warning("Flashing already in progress.")
            return
        self.state.console.clear()
        logging.info("Starting flashing process...")
        # Generate device dir and log file
        device_dir = get_device_dir(
            self.state.device_name or None,
            self.state.mac_address,
        )
        flash_log_path = get_flash_log_path(device_dir)
        self.state.set_log_file(flash_log_path)
        self.flashing_thread = FlashingThread(
            self.state.firmware, self.state.chip_port
        )

        self.flashing_thread.finished_signal.connect(self.handle_flash_completion)
        self.flashing_thread.start()

    def handle_flash_completion(self, success):
        self.cleanup_flashing_thread()
        self.state.close_log_file()

        if success:
            self.state.test_module.increment_flash_count()
            if self.state.test_module.should_run_test():
                self.start_test_thread()
            else:
                self.state.show_success_popup("Flashing completed successfully!")

    def start_test_thread(self):
        # Set up testing log file
        device_dir = get_device_dir(
            self.state.device_name or None,
            self.state.mac_address,
        )
        test_log_path = get_testing_log_path(device_dir)
        self.state.set_log_file(test_log_path)

        # Create a new TestThread with the latest model
        self.test_thread = TestThread(self.state.test_module)
        self.test_thread.test_timeout_signal.connect(self.state.show_error_popup)
        self.test_thread.test_success_signal.connect(self.state.show_success_popup)
        self.test_thread.test_started_signal.connect(self.state.show_testing_popup)
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
        if not self.state.chip_port:
            logging.error("No chip port selected!")
            return

        # If port changed since the log thread was created, tear down the old one
        if self.log_thread is not None and self.log_thread._port != self.state.chip_port:
            logging.info("Port changed, restarting log thread...")
            self.stop_logs()

        self.state.console.clear()
        logging.info("Starting log monitoring...")

        if self.log_thread is None:
            self.log_thread = LogThread(self.state.chip_port)
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
        self.state.close_testing_popup()
        self.stop_logs()
        self.state.close_log_file()
        # self.test_thread = None

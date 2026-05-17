# filepath: esp_flasher/threads/test_thread.py
import logging
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import re


class TestThread(QObject):
    test_success_signal = pyqtSignal(str)
    test_started_signal = pyqtSignal(str)
    test_stopped_signal = pyqtSignal()
    test_timeout_signal = pyqtSignal(str)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)

    def start_test(self):
        self.model.is_testing = True
        self._timer.setInterval(self.model.timeout_seconds * 1000)
        self._timer.start()
        self.test_started_signal.emit("Device test started...")

    def stop_test(self):
        self.model.is_testing = False
        self._timer.stop()
        self.test_stopped_signal.emit()

    def process_log_line(self, line):
        if not self.model.is_testing:
            return
        if self.model.regex and isinstance(self.model.regex, str):
            if re.search(self.model.regex, line):
                logging.info("Result: PASS!")
                self.stop_test()
                self.test_success_signal.emit("Device testing passed!")

    def _on_timeout(self):
        if self.model.is_testing:
            logging.error("Result: FAIL!")
            self.stop_test()
            self.test_timeout_signal.emit("Device testing failed!")

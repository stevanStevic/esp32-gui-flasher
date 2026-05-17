from PyQt5.QtCore import QThread, pyqtSignal
import logging

from esp_flasher.core.serial import read_serial_lines
from esp_flasher.core.errors import EspFlasherError


class LogThread(QThread):
    error_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)  # Add signal to emit log lines

    def __init__(self, port):
        super().__init__()
        self._port = port
        self._running = False

    def run(self):
        """Reads logs from the ESP device in a non-blocking way."""
        self._running = True

        try:
            for line in read_serial_lines(
                self._port, should_stop=lambda: not self._running
            ):
                if not self._running:
                    break
                logging.info(line)
                self.log_signal.emit(line)
        except EspFlasherError as e:
            self.error_signal.emit(str(e))
        except Exception as e:
            self.error_signal.emit(f"Log Error: {str(e)}")

    def stop_logging(self):
        """Stops log monitoring gracefully."""
        if self.isRunning():
            self._running = False
            self.wait()  # Ensure thread exits properly
            logging.info("Logging stopped.")

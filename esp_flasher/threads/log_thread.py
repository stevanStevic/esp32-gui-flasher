from PyQt5.QtCore import QThread, pyqtSignal
import serial
import time
import logging


class LogThread(QThread):
    error_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)  # Add signal to emit log lines

    def __init__(self, port):
        super().__init__()
        self._port = port
        self._running = False
        self._default_color = "white"

    def run(self):
        """Reads logs from the ESP device in a non-blocking way."""
        self._running = True

        try:
            with serial.Serial(self._port, baudrate=115200, timeout=1) as serial_port:
                # Prevent ESP32 from staying in bootloader mode
                serial_port.setDTR(False)
                serial_port.setRTS(False)
                time.sleep(0.1)  # Give it a moment to settle

                while self._running:
                    if serial_port.in_waiting > 0:
                        raw = serial_port.readline()
                        text = raw.decode(errors="ignore").strip()
                        logging.info(text)

                        self.log_signal.emit(text)  # Emit log line for test controller
        except serial.SerialException as e:
            self.error_signal.emit(f"Serial Error: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"Log Error: {str(e)}")

    def start_logging(self):
        """Starts the logging process inside the thread."""
        if not self.isRunning():
            self.start()  # Start the QThread

    def stop_logging(self):
        """Stops log monitoring gracefully."""
        if self.isRunning():
            self._running = False
            self.wait()  # Ensure thread exits properly
            logging.info("Logging stopped.")

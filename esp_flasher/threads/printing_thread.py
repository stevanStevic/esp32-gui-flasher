from PyQt5.QtCore import QThread, pyqtSignal


class PrintingThread(QThread):
    success_signal = pyqtSignal(str)  # Signal for success messages
    error_signal = pyqtSignal(str)  # Signal for error messages

    def __init__(self, printer_port, device_name):
        super().__init__()
        self._printer_port = printer_port
        self._device_name = device_name

    def run(self):
        """Runs the print job safely and emits signals based on the outcome."""
        try:
            from esp_flasher.backend.printer import print_message

            if not self._device_name:
                self.error_signal.emit(
                    "Error: Device name is missing. Please register the device first."
                )
                return

            print_message(self._printer_port, self._device_name)
            self.success_signal.emit(f"Printed successfully: {self._device_name}")

        except Exception as e:
            self.error_signal.emit(f"Printing Error: {str(e)}")

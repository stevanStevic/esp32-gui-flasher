from PyQt5.QtCore import QThread, pyqtSignal


class FlashingThread(QThread):
    success_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)  # Signal to indicate success

    def __init__(self, firmware, port):
        super().__init__()
        self._firmware = firmware
        self._port = port

    def run(self):
        """Executes the flashing process safely."""
        try:
            from esp_flasher.__main__ import run_esp_flasher

            run_esp_flasher(self._port, self._firmware)

            self.success_signal.emit("Flashing completed successfully!")
            self.finished_signal.emit(True)  # Notify ActionsSection of success
        except Exception as e:
            self.error_signal.emit(f"Flashing Error: {str(e)}")
            self.finished_signal.emit(False)

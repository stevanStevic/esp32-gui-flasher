import logging
from PyQt5.QtCore import QThread, pyqtSignal
from esp_flasher.__main__ import run_esp_flasher


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

            run_esp_flasher(self._port, self._firmware, baud_rate=460800)

            logging.info("Flashing completed successfully!")
            self.finished_signal.emit(True)  # Notify ActionsSection of success
        except Exception as e:
            logging.error(f"Flashing Error: {str(e)}")
            self.finished_signal.emit(False)

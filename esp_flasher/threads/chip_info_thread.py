import logging
from PyQt5.QtCore import QThread, pyqtSignal


class ChipInfoThread(QThread):
    mac_address_signal = pyqtSignal(str)  # Signal to send MAC address

    def __init__(self, port):
        super().__init__()
        self._port = port

    def run(self):
        try:
            from esp_flasher.cli.chip_info import dump_info

            info = dump_info(self._port)

            self.mac_address_signal.emit(info.mac)  # Emit MAC address
        except Exception as e:
            logging.error(f"Error retrieving chip info: {str(e)}")

import logging
from PyQt5.QtCore import QThread, pyqtSignal

from esp_flasher.core.chip import get_chip_info


class ChipInfoThread(QThread):
    mac_address_signal = pyqtSignal(str)  # Signal to send MAC address

    def __init__(self, port):
        super().__init__()
        self._port = port

    def run(self):
        try:
            info = get_chip_info(self._port)

            logging.info("Chip Information:")
            logging.info(f" - Chip Family: {info.family}")
            logging.info(f" - Model: {info.model}")
            logging.info(f" - MAC Address: {info.mac}")

            if hasattr(info, "num_cores"):
                logging.info(f" - Cores: {info.num_cores}")
                logging.info(f" - CPU Frequency: {info.cpu_frequency}")
                logging.info(f" - Bluetooth: {'YES' if info.has_bluetooth else 'NO'}")
                logging.info(f" - Embedded Flash: {'YES' if info.has_embedded_flash else 'NO'}")
                logging.info(
                    f" - Factory-Calibrated ADC: {'YES' if info.has_factory_calibrated_adc else 'NO'}"
                )

            self.mac_address_signal.emit(info.mac)
        except Exception as e:
            logging.error(f"Error retrieving chip info: {str(e)}")

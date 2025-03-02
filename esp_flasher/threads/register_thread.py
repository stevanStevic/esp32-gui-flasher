from PyQt5.QtCore import QThread, pyqtSignal


class RegisterThread(QThread):
    device_name_signal = pyqtSignal(str)  # Signal for successful registration
    error_signal = pyqtSignal(str)  # Signal for error handling

    def __init__(self, api_endpoint, api_key, api_secret, mac_address):
        super().__init__()
        self._api_endpoint = api_endpoint
        self._api_key = api_key
        self._api_secret = api_secret
        self._mac = mac_address

    def run(self):
        """Publishes MAC address and handles API response."""
        try:
            from esp_flasher.backend.api_client import publish_mac_address

            device_name, error_message = publish_mac_address(
                self._api_endpoint, self._api_key, self._api_secret, self._mac
            )

            if device_name:
                self.device_name_signal.emit(
                    device_name
                )  # Emit device name if successful
            else:
                self.error_signal.emit(error_message)  # Emit error if request failed

        except Exception as e:
            self.error_signal.emit(f"Unexpected error: {e}")  # Handle unexpected errors

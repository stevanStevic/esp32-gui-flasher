from PyQt5.QtCore import QThread, pyqtSignal

from esp_flasher.backend.printer import get_printer


class PrintingThread(QThread):
    success_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, printer_name, message):
        super().__init__()
        self.printer_name = printer_name
        self.message = message

    def run(self):
        """Runs the print job safely."""
        try:
            printer = get_printer(self.printer_name)
            result = printer.print_label(self.message)
            self.success_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(f"Printing Error: {str(e)}")

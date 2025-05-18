import logging
from PyQt5.QtCore import QThread, pyqtSignal
from esp_flasher.backend.printer import get_printer


class PrintingThread(QThread):
    success_signal = pyqtSignal(str)

    def __init__(
        self,
        printer_name,
        message,
        label_width=62,
        x_offset=100,
        y_offset=100,
        text_rotation=270,
        font=20,
    ):
        super().__init__()
        self.printer_name = printer_name
        self.message = message
        self.label_width = label_width
        self.text_rotation = text_rotation
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.font = font

    def run(self):
        """Runs the print job safely with configurable parameters."""
        try:
            printer = get_printer(self.printer_name)
            result = printer.print_label(
                self.message,
                label_width=self.label_width,
                x_offset=self.x_offset,
                y_offset=self.y_offset,
                text_rotation=self.text_rotation,
                font_size=self.font,
            )
            logging.info(result)
        except Exception as e:
            logging.error(f"Printing Error: {str(e)}")

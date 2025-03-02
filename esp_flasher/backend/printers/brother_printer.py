from esp_flasher.backend.printers.base_printer import BasePrinter
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send


class BrotherQLPrinter(BasePrinter):
    """Printer implementation for Brother QL-600 on Linux."""

    def __init__(self, printer_name):
        self.printer_name = printer_name

    def print_label(self, message: str):
        """Prints a label using Brother QL-600."""
        try:
            ql = BrotherQLRaster("QL-600B")
            instructions = convert(
                ql,
                [message],
                label="62",
                rotate=0,
                threshold=70.0,
                dither=True,
                compress=False,
                dpi_600=False,
            )
            send(instructions, self.printer_name)
            return "Print job sent successfully."
        except Exception as err:
            return f"Error printing label: {err}"

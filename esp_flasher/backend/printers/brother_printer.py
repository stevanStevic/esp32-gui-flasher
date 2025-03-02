from esp_flasher.backend.printers.base_printer import BasePrinter
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send


class BrotherQLPrinter(BasePrinter):
    """Printer implementation for Linux with configurable label settings."""

    def __init__(
        self,
        printer_name,
    ):
        self.printer_name = printer_name

    def print_label(
        self,
        message: str,
        label_width=62,  # Label width
        x_offset=100,  # Horizontal text offset
        y_offset=100,  # Vertical text offset
        text_rotation=270,  # Rotation of text in degrees
        font_size=20,  # Font size in points
    ):
        """Prints a label using Brother QL-600 on Linux with configurable label dimensions."""
        try:
            ql = BrotherQLRaster("QL-600B")
            instructions = convert(
                ql,
                [message],
                label=str(label_width),  # Set label width dynamically
                rotate=text_rotation,  # Apply text rotation
                threshold=x_offset,
                dither=True,
                compress=False,
                dpi_600=False,
            )
            send(instructions, self.printer_name)
            return "Print job sent successfully."
        except Exception as err:
            return f"Error printing label: {err}"

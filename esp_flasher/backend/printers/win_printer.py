import win32ui
import win32con
from esp_flasher.backend.printers.base_printer import BasePrinter


class WindowsPrinter(BasePrinter):
    """Printer implementation for Windows with configurable label settings."""

    def __init__(self, printer_name):
        self.printer_name = printer_name
        self.font_weight = win32con.FW_NORMAL  # Font weight (e.g., normal, bold)

    def print_label(
        self,
        message: str,
        label_width=62,  # Label width
        x_offset=100,  # Horizontal text offset
        y_offset=100,  # Vertical text offset
        text_rotation=270,  # Rotation of text in degrees
        font_size=20,  # Font size in points
    ):
        """Prints a label using Windows printing API with configurable label dimensions."""
        try:
            hprinter_dc = win32ui.CreateDC()
            hprinter_dc.CreatePrinterDC(self.printer_name)

            # Set page size based on label dimensions (convert mm to pixels at 300 DPI)
            dpi = hprinter_dc.GetDeviceCaps(win32con.LOGPIXELSX)  # Get DPI

            # Page setup
            hprinter_dc.StartDoc("Label Print")
            hprinter_dc.StartPage()

            # Apply text rotation and font settings
            font = win32ui.CreateFont(
                {
                    "height": -int(font_size * dpi / 72),  # Convert to pixels
                    "weight": self.font_weight,
                    # Rotation in tenths of degrees
                    "escapement": text_rotation * 10,
                }
            )
            hprinter_dc.SelectObject(font)

            # Print text with offsets
            hprinter_dc.TextOut(x_offset, y_offset, message)

            hprinter_dc.EndPage()
            hprinter_dc.EndDoc()
            hprinter_dc.DeleteDC()

            return "Print job sent successfully."
        except Exception as err:
            return f"Error printing label: {err}"

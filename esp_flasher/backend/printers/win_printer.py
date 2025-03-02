import win32con
import win32ui
from esp_flasher.backend.printers.base_printer import BasePrinter


class WindowsPrinter(BasePrinter):
    """Printer implementation for Windows with configurable page setup."""

    def __init__(
        self,
        printer_name,
        label_width=62,
        orientation="landscape",
        x_offset=10,
        y_offset=10,
    ):
        self.printer_name = printer_name
        self.label_width = label_width  # Width in mm
        self.orientation = orientation  # "portrait" or "landscape"
        self.x_offset = x_offset  # Horizontal text offset
        self.y_offset = y_offset  # Vertical text offset

    def print_label(self, message: str):
        """Prints a label using Windows printing API with page setup."""
        try:
            hprinter_dc = win32ui.CreateDC()
            hprinter_dc.CreatePrinterDC(self.printer_name)

            # Page setup
            hprinter_dc.StartDoc("Label Print")
            hprinter_dc.StartPage()

            # Adjust printing based on orientation
            if self.orientation == "landscape":
                hprinter_dc.SetMapMode(win32con.MM_ANISOTROPIC)
                hprinter_dc.SetWindowExt(
                    (self.label_width * 10, 100)
                )  # Scale for width

            # Print text with offsets
            hprinter_dc.TextOut(self.x_offset, self.y_offset, message)

            hprinter_dc.EndPage()
            hprinter_dc.EndDoc()
            hprinter_dc.DeleteDC()

            return "Print job sent successfully."
        except Exception as err:
            return f"Error printing label: {err}"

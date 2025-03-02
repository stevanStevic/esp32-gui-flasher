import platform
from esp_flasher.backend.printers.brother_printer import BrotherQLPrinter
from esp_flasher.backend.printers.win_printer import WindowsPrinter


def get_printer(printer_name):
    """Returns the correct printer implementation based on OS."""
    if platform.system() == "Linux":
        return BrotherQLPrinter(printer_name)
    elif platform.system() == "Windows":
        return WindowsPrinter(printer_name)
    else:
        raise ValueError("Unsupported OS for printing")

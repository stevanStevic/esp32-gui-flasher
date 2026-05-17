import platform
from esp_flasher.modules.registration_printing.printers.brother_printer import BrotherQLPrinter


def get_printer(printer_name):
    """Returns the correct printer implementation based on OS."""
    if platform.system() == "Linux":
        return BrotherQLPrinter(printer_name)
    elif platform.system() == "Windows":
        from esp_flasher.modules.registration_printing.printers.win_printer import WindowsPrinter
        return WindowsPrinter(printer_name)
    else:
        raise ValueError("Unsupported OS for printing")

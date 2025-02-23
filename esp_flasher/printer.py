import argparse
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send

from esp_flasher.common import Esp_flasherError


def print_message(
    port: str, message: str, printer_model: str = "QL-600B", label: str = "62"
):
    """
    Prints a message using a Brother QL-600B thermal printer.

    Args:
        port (str): Printer port (e.g., 'COM3' for Windows or '/dev/usb/lp0' for Linux).
        message (str): The message to print.
        printer_model (str, optional): The model of the Brother printer. Defaults to 'QL-600B'.
        label (str, optional): The label type (default: '62' for 62mm continuous roll).

    Returns:
        None: Prints the message and outputs success or error messages.
    """
    try:
        ql = BrotherQLRaster(printer_model)
        instructions = convert(
            ql,
            [message],  # Message as input
            label=label,  # Label type (default: 62mm continuous roll)
            rotate=0,  # No rotation
            threshold=70.0,  # Default threshold
            dither=True,  # Enable dithering
            compress=False,  # No compression
            dpi_600=False,  # Use 300dpi mode
        )
        send(instructions, port)
    except Exception as err:
        raise Esp_flasherError(f"Error while printing {message}: {err}") from err

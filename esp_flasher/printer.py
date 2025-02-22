import argparse
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send


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
        print(message)
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
        print("Message printed successfully!")
    except Exception as e:
        print(f"Error: {e}")

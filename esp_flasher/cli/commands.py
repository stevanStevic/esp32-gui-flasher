import argparse
from esp_flasher.core.const import __version__


def parse_args(argv):
    parser = argparse.ArgumentParser(prog=f"esp_flasher {__version__}")
    parser.add_argument(
        "--gui", action="store_true",
        help="Launch the GUI. When set, all other flags are ignored."
    )
    parser.add_argument("-p", "--port", help="Select the USB/COM port for uploading.")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--upload-baud-rate", type=int, default=115200, help="Baud rate for uploading"
    )
    parser.add_argument("--firmware", help="(ESP32-only) Firmware to flash")
    parser.add_argument(
        "--no-erase", action="store_true", help="Do not erase flash before flashing"
    )
    parser.add_argument("--show-logs", action="store_true", help="Only show logs")
    parser.add_argument(
        "--info-dump", action="store_true", help="Only show device info"
    )
    parser.add_argument(
        "--enable-device-registration-and-printing",
        action="store_true",
        help="Enable device registration and printing section in the GUI.",
    )
    return parser.parse_args(argv[1:])

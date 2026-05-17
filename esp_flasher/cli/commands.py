import argparse

from esp_flasher.core.const import __version__, DEFAULT_BAUD_RATE


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="esp_flasher",
        description=f"ESP Flasher CLI v{__version__}",
    )

    # ── Top-level flags (before subcommand) ──────────────────────────
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the GUI. When set, all subcommands are ignored.",
    )
    parser.add_argument(
        "--load-module",
        action="append",
        default=[],
        dest="load_modules",
        metavar="PATH",
        help="(GUI only) Path to a GUIModule plugin. May be repeated.",
    )

    # ── Subcommands ──────────────────────────────────────────────────
    subparsers = parser.add_subparsers(dest="command")

    # -- info ----------------------------------------------------------
    info_parser = subparsers.add_parser("info", help="Read and display chip info.")
    info_parser.add_argument(
        "-p", "--port", required=True, help="Serial port (e.g. /dev/ttyUSB0)."
    )

    # -- flash ---------------------------------------------------------
    flash_parser = subparsers.add_parser("flash", help="Flash firmware onto the ESP.")
    flash_parser.add_argument(
        "-p", "--port", required=True, help="Serial port (e.g. /dev/ttyUSB0)."
    )
    flash_parser.add_argument(
        "--firmware", required=True, help="Path to the firmware release .zip file."
    )
    flash_parser.add_argument(
        "--baud",
        type=int,
        default=DEFAULT_BAUD_RATE,
        dest="baud_rate",
        help=f"Upload baud rate (default: {DEFAULT_BAUD_RATE}).",
    )

    # -- logs ----------------------------------------------------------
    logs_parser = subparsers.add_parser(
        "logs", help="Stream device logs (blocks until Ctrl+C)."
    )
    logs_parser.add_argument(
        "-p", "--port", required=True, help="Serial port (e.g. /dev/ttyUSB0)."
    )

    # -- test ----------------------------------------------------------
    test_parser = subparsers.add_parser(
        "test", help="Flash firmware, then run a log-based pass/fail test."
    )
    test_parser.add_argument(
        "-p", "--port", required=True, help="Serial port (e.g. /dev/ttyUSB0)."
    )
    test_parser.add_argument(
        "--firmware", required=True, help="Path to the firmware release .zip file."
    )
    test_parser.add_argument(
        "--regex", required=True, help="Regex pattern to match in device logs."
    )
    test_parser.add_argument(
        "--timeout",
        type=int,
        required=True,
        help="Seconds to wait for the regex match before failing.",
    )
    test_parser.add_argument(
        "--baud",
        type=int,
        default=DEFAULT_BAUD_RATE,
        dest="baud_rate",
        help=f"Upload baud rate (default: {DEFAULT_BAUD_RATE}).",
    )

    return parser.parse_args(argv[1:])

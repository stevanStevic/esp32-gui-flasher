"""CLI command handlers.

Each public function corresponds to a subcommand and receives an
``argparse.Namespace``.  Handlers are thin wrappers around the *core*
layer — they contain no GUI or threading logic.
"""

import re
import time

from esp_flasher.core.chip import get_chip_info
from esp_flasher.core.flasher import run_esp_flasher
from esp_flasher.core.errors import EspFlasherError
from esp_flasher.core.serial import read_serial_lines


# ── info ─────────────────────────────────────────────────────────────

def handle_info(args):
    """Read and display chip information."""
    info = get_chip_info(args.port)

    print("Chip Information:")
    print(f"  Chip Family : {info.family}")
    print(f"  Model       : {info.model}")
    print(f"  MAC Address : {info.mac}")

    if hasattr(info, "num_cores"):
        print(f"  Cores       : {info.num_cores}")
        print(f"  CPU Freq    : {info.cpu_frequency}")
        print(f"  Bluetooth   : {'YES' if info.has_bluetooth else 'NO'}")
        print(f"  Embed Flash : {'YES' if info.has_embedded_flash else 'NO'}")
        print(
            f"  Calibr. ADC : "
            f"{'YES' if info.has_factory_calibrated_adc else 'NO'}"
        )

    return info


# ── flash ────────────────────────────────────────────────────────────

def handle_flash(args):
    """Flash firmware onto the ESP chip."""
    run_esp_flasher(args.port, args.firmware, baud_rate=args.baud_rate)
    print("Flashing completed successfully.")


# ── logs ─────────────────────────────────────────────────────────────

def handle_logs(args):
    """Stream device logs until interrupted with Ctrl+C."""
    print(f"Streaming logs from {args.port}  (Ctrl+C to stop) …")
    try:
        for line in read_serial_lines(args.port):
            print(line)
    except KeyboardInterrupt:
        print("\nLog streaming stopped.")


# ── test ─────────────────────────────────────────────────────────────

def handle_test(args):
    """Flash firmware, then watch logs for a regex match within a timeout.

    Exit codes:
        0 – pattern matched (PASS)
        1 – timeout expired without match (FAIL)
    """
    # 1. Flash
    print("Step 1/2: Flashing firmware …")
    run_esp_flasher(args.port, args.firmware, baud_rate=args.baud_rate)
    print("Flashing completed successfully.")

    # 2. Watch logs
    pattern = re.compile(args.regex)
    deadline = time.time() + args.timeout
    print(
        f"Step 2/2: Watching logs for /{args.regex}/ "
        f"(timeout {args.timeout}s) …"
    )

    for line in read_serial_lines(args.port):
        if time.time() >= deadline:
            break
        print(line)
        if pattern.search(line):
            print("\n✅ PASS — pattern matched.")
            return True

    print("\n❌ FAIL — timeout expired without a match.")
    return False

import time

import serial
import esptool

from esp_flasher.core.errors import EspFlasherError


def list_serial_ports():
    return esptool.get_port_list()


def read_serial_lines(port, baudrate=115200, timeout=1, should_stop=None):
    """Open a serial port and yield decoded, stripped lines.

    Configures DTR/RTS for ESP chips and yields non-empty lines
    until the caller stops iterating (e.g. via ``break``) or
    *should_stop* returns ``True``.

    Args:
        port: Serial port path.
        baudrate: Baud rate (default 115200).
        timeout: Read timeout in seconds (default 1).
        should_stop: Optional callable returning ``True`` to signal
            the generator to exit.  Checked every loop iteration so
            the caller can stop even when no data arrives.

    Raises:
        EspFlasherError: on serial communication failure.
    """
    try:
        with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
            ser.setDTR(False)
            ser.setRTS(False)
            time.sleep(0.1)

            while True:
                if should_stop is not None and should_stop():
                    break
                if ser.in_waiting > 0:
                    raw = ser.readline()
                    text = raw.decode(errors="ignore").strip()
                    if text:
                        yield text
                else:
                    time.sleep(0.01)  # avoid busy-wait when idle
    except serial.SerialException as exc:
        raise EspFlasherError(f"Serial error: {exc}") from exc

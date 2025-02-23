from __future__ import print_function

import argparse
import sys
import time
from datetime import datetime

import esptool
import serial

from esp_flasher import const
from esp_flasher.common import (
    Esp_flasherError,
    chip_run_stub,
    configure_write_flash_args,
    detect_chip,
    read_chip_info,
)

from esp_flasher.helpers import list_serial_ports
from esp_flasher.const import DEFAULT_BAUD_RATE

# Execute or stop the logs
RUN_LOG = True


def parse_args(argv):
    parser = argparse.ArgumentParser(prog=f"esp_flasher {const.__version__}")
    parser.add_argument("-p", "--port", help="Select the USB/COM port for uploading.")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--upload-baud-rate",
        type=int,
        default=DEFAULT_BAUD_RATE,
        help="Baud rate to upload with (not for logging)",
    )
    parser.add_argument(
        "--firmware",
        help="(ESP32-only) Firmware to flash",
    )
    parser.add_argument(
        "--no-erase", help="Do not erase flash before flashing", action="store_true"
    )
    parser.add_argument("--show-logs", help="Only show logs", action="store_true")
    parser.add_argument(
        "--info-dump", help="Only show device info", action="store_true"
    )

    return parser.parse_args(argv[1:])


def select_port(args):
    if args.port is not None:
        print(f"Using '{args.port}' as serial port.")
        return args.port
    ports = list_serial_ports()
    if not ports:
        raise Esp_flasherError("No serial port found!")
    if len(ports) != 1:
        print("Found more than one serial port:")
        for port, desc in ports:
            print(f" * {port} ({desc})")
        print("Please choose one with the --port argument.")
        raise Esp_flasherError
    print(f"Auto-detected serial port: {ports[0][0]}")
    return ports[0][0]


def stop_logs():
    global RUN_LOG
    RUN_LOG = False


def show_logs(port):
    print("Showing logs:")
    global RUN_LOG
    RUN_LOG = True
    serial_port = serial.Serial(port, baudrate=115200)
    with serial_port:
        while RUN_LOG:
            try:
                raw = serial_port.readline()
            except serial.SerialException:
                print("Serial port closed!")
                return
            text = raw.decode(errors="ignore")
            line = text.replace("\r", "").replace("\n", "")
            time_ = datetime.now().time().strftime("[%H:%M:%S]")
            message = time_ + line
            try:
                print(message)
            except UnicodeEncodeError:
                print(message.encode("ascii", "backslashreplace"))
        serial_port.close()


def dump_info(port):
    try:
        chip = detect_chip(port)
        info = read_chip_info(chip)

        print()
        print("Chip Info:")
        print(f" - Chip Family: {info.family}")
        print(f" - Chip Model: {info.model}")
        print(f" - Number of Cores: {info.num_cores}")
        print(f" - Max CPU Frequency: {info.cpu_frequency}")
        print(f" - Has Bluetooth: {'YES' if info.has_bluetooth else 'NO'}")
        print(f" - Has Embedded Flash: {'YES' if info.has_embedded_flash else 'NO'}")
        print(
            f" - Has Factory-Calibrated ADC: {'YES' if info.has_factory_calibrated_adc else 'NO'}"
        )
        print(f" - MAC Address: {info.mac}")

        chip._port.close()
    except Exception as e:
        pass


def run(argv):
    args = parse_args(argv)
    port = select_port(args)

    if args.show_logs:
        show_logs(port)
        return

    if args.info_dump:
        dump_info(port)
        return

    run_esp_flasher(port, args.firmware, args.upload_baud_rate, args.no_erase)


def run_esp_flasher(port, firmware, baud_rate=DEFAULT_BAUD_RATE, no_erase=True):
    chip = detect_chip(port)

    stub_chip = chip_run_stub(chip)
    flash_size = None

    if baud_rate != 115200:
        try:
            stub_chip.change_baud(baud_rate)
        except esptool.FatalError as err:
            raise Esp_flasherError(
                f"Error changing ESP upload baud rate: {err}"
            ) from err

    mock_args = configure_write_flash_args(firmware)

    print(f" - Flash Mode: {mock_args.flash_mode}")
    print(f" - Flash Frequency: {mock_args.flash_freq.upper()}Hz")
    print(f" - Flash Size: {mock_args.flash_size}")

    try:
        stub_chip.flash_set_parameters(esptool.flash_size_bytes(mock_args.flash_size))
    except esptool.FatalError as err:
        raise Esp_flasherError(f"Error setting flash parameters: {err}") from err

    if not no_erase:
        try:
            esptool.erase_flash(stub_chip, mock_args)
        except esptool.FatalError as err:
            raise Esp_flasherError(f"Error while erasing flash: {err}") from err

    try:
        esptool.write_flash(stub_chip, mock_args)
    except esptool.FatalError as err:
        raise Esp_flasherError(f"Error while writing flash: {err}") from err

    print("Hard Resetting...")
    stub_chip.hard_reset()

    print("Done! Flashing is complete!")
    print()

    if baud_rate != 115200:
        # pylint: disable=protected-access
        stub_chip._port.baudrate = 115200
        time.sleep(0.05)  # get rid of crap sent during baud rate change
        # pylint: disable=protected-access
        stub_chip._port.flushInput()

    # Close the serial connection
    chip._port.close()

    # pylint: disable=protected-access
    show_logs(port)


def main():
    try:
        if len(sys.argv) <= 1:
            from esp_flasher import gui

            return gui.main() or 0
        return run(sys.argv) or 0
    except Esp_flasherError as err:
        msg = str(err)
        if msg:
            print(msg)
        return 1
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(main())

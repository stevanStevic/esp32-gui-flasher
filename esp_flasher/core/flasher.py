import time
import esptool
from esp_flasher.helpers.utils import Esp_flasherError
from esp_flasher.core.chip_utils import (
    chip_run_stub,
    detect_chip,
)
from esp_flasher.core.firmware_utils import configure_write_flash_args


def run_esp_flasher(port, firmware, baud_rate=115200, no_erase=True):
    chip = detect_chip(port)
    stub_chip = chip_run_stub(chip)

    if baud_rate != 115200:
        try:
            stub_chip.change_baud(baud_rate)
        except esptool.FatalError as err:
            raise Esp_flasherError(f"Error changing ESP upload baud rate: {err}")

    mock_args = configure_write_flash_args(firmware)

    print(f" - Flash Mode: {mock_args.flash_mode}")
    print(f" - Flash Frequency: {mock_args.flash_freq.upper()}Hz")
    print(f" - Flash Size: {mock_args.flash_size}")

    try:
        stub_chip.flash_set_parameters(esptool.flash_size_bytes(mock_args.flash_size))
    except esptool.FatalError as err:
        raise Esp_flasherError(f"Error setting flash parameters: {err}")

    if not no_erase:
        try:
            esptool.erase_flash(stub_chip, mock_args)
        except esptool.FatalError as err:
            raise Esp_flasherError(f"Error while erasing flash: {err}")

    try:
        esptool.write_flash(stub_chip, mock_args)
    except esptool.FatalError as err:
        raise Esp_flasherError(f"Error while writing flash: {err}")

    print("Resetting device...")
    stub_chip.hard_reset()
    print("Flashing completed successfully!")

    if baud_rate != 115200:
        stub_chip._port.baudrate = 115200
        time.sleep(0.05)
        stub_chip._port.flushInput()

    chip._port.close()

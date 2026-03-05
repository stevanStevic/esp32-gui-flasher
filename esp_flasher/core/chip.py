import esptool

from esp_flasher.core.errors import EspFlasherError
from esp_flasher.helpers.utils import prevent_print


class EsptoolFlashArgs:
    def __init__(
        self,
        chip,
        write_flash_args,
        flash_size,
        addr_filename,
        flash_mode,
        flash_freq,
        stub,
        before,
        after,
    ):
        self.chip = chip
        self.write_flash_args = write_flash_args
        self.flash_size = flash_size
        self.addr_filename = addr_filename
        self.flash_mode = flash_mode
        self.flash_freq = flash_freq
        self.no_stub = not stub
        self.before = before
        self.after = after


class ChipInfo:
    def __init__(self, family, model, mac):
        self.family = family
        self.model = model
        self.mac = mac

    def as_dict(self):
        return {
            "family": self.family,
            "model": self.model,
            "mac": self.mac,
        }


class ESP32ChipInfo(ChipInfo):
    def __init__(
        self,
        model,
        mac,
        num_cores,
        cpu_frequency,
        has_bluetooth,
        has_embedded_flash,
        has_factory_calibrated_adc,
    ):
        super().__init__("ESP32", model, mac)
        self.num_cores = num_cores
        self.cpu_frequency = cpu_frequency
        self.has_bluetooth = has_bluetooth
        self.has_embedded_flash = has_embedded_flash
        self.has_factory_calibrated_adc = has_factory_calibrated_adc

    def as_dict(self):
        data = ChipInfo.as_dict(self)
        data.update(
            {
                "num_cores": self.num_cores,
                "cpu_frequency": self.cpu_frequency,
                "has_bluetooth": self.has_bluetooth,
                "has_embedded_flash": self.has_embedded_flash,
                "has_factory_calibrated_adc": self.has_factory_calibrated_adc,
            }
        )
        return data


def read_chip_property(func, *args, **kwargs):
    try:
        return prevent_print(func, *args, **kwargs)
    except esptool.FatalError as err:
        raise EspFlasherError(f"Reading chip details failed: {err}") from err


def read_chip_info(chip):
    mac = ":".join(f"{x:02X}" for x in read_chip_property(chip.read_mac))
    if isinstance(chip, esptool.ESP32ROM):
        model = read_chip_property(chip.get_chip_description)
        features = read_chip_property(chip.get_chip_features)
        num_cores = 2 if "Dual Core" in features else 1
        frequency = next((x for x in ("160MHz", "240MHz") if x in features), "80MHz")
        has_bluetooth = "BT" in features
        has_embedded_flash = "Embedded Flash" in features
        has_factory_calibrated_adc = "VRef calibration in efuse" in features
        return ESP32ChipInfo(
            model,
            mac,
            num_cores,
            frequency,
            has_bluetooth,
            has_embedded_flash,
            has_factory_calibrated_adc,
        )

    raise EspFlasherError(f"Unknown chip type {type(chip)}")


def chip_run_stub(chip):
    try:
        return chip.run_stub()
    except esptool.FatalError as err:
        raise EspFlasherError(f"Error putting ESP in stub flash mode: {err}") from err


def detect_chip(port, baud=115200):
    """Detect ESP chip type."""
    try:
        chip = esptool.get_default_connected_device(
            serial_list=[port], port=port, connect_attempts=1, initial_baud=baud
        )
        return chip
    except esptool.FatalError as err:
        raise EspFlasherError(f"ESP Chip Auto-Detection failed: {err}") from err


def get_chip_info(port):
    """Detect the chip, read its info, and close the port.

    Returns:
        A ChipInfo (or subclass) instance.

    Raises:
        EspFlasherError: on detection or communication failure.
    """
    chip = detect_chip(port)
    try:
        return read_chip_info(chip)
    finally:
        chip._port.close()

import struct
import esptool

from esp_flasher.helpers.utils import prevent_print, Esp_flasherError


class MockEsptoolArgs:
    def __init__(self, flash_size, addr_filename, flash_mode, flash_freq):
        self.compress = True
        self.no_compress = False
        self.flash_size = flash_size
        self.addr_filename = addr_filename
        self.flash_mode = flash_mode
        self.flash_freq = flash_freq
        self.no_stub = False
        self.verify = False
        self.erase_all = False
        self.encrypt = False
        self.encrypt_files = None


class ChipInfo:
    def __init__(self, family, model, mac):
        self.family = family
        self.model = model
        self.mac = mac
        self.is_esp32 = None

    def as_dict(self):
        return {
            "family": self.family,
            "model": self.model,
            "mac": self.mac,
            "is_esp32": self.is_esp32,
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


class ESP8266ChipInfo(ChipInfo):
    def __init__(self, model, mac, chip_id):
        super().__init__("ESP8266", model, mac)
        self.chip_id = chip_id

    def as_dict(self):
        data = ChipInfo.as_dict(self)
        data.update(
            {
                "chip_id": self.chip_id,
            }
        )
        return data


def read_chip_property(func, *args, **kwargs):
    try:
        return prevent_print(func, *args, **kwargs)
    except esptool.FatalError as err:
        raise Esp_flasherError(f"Reading chip details failed: {err}") from err


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

    raise Esp_flasherError(f"Unknown chip type {type(chip)}")


def chip_run_stub(chip):
    try:
        return chip.run_stub()
    except esptool.FatalError as err:
        raise Esp_flasherError(f"Error putting ESP in stub flash mode: {err}") from err


def detect_flash_size(stub_chip):
    flash_id = read_chip_property(stub_chip.flash_id)
    return esptool.DETECTED_FLASH_SIZES.get(flash_id >> 16, "4MB")


def read_firmware_info(firmware):
    header = firmware.read(4)
    firmware.seek(0)

    magic, _, flash_mode_raw, flash_size_freq = struct.unpack("BBBB", header)
    if magic != esptool.ESPLoader.ESP_IMAGE_MAGIC:
        raise Esp_flasherError(
            f"The firmware binary is invalid (magic byte={magic:02X}, should be {esptool.ESPLoader.ESP_IMAGE_MAGIC:02X})"
        )
    flash_freq_raw = flash_size_freq & 0x0F
    flash_mode = {0: "qio", 1: "qout", 2: "dio", 3: "dout"}.get(flash_mode_raw)
    flash_freq = {0: "40m", 1: "26m", 2: "20m", 0xF: "80m"}.get(flash_freq_raw)
    return flash_mode, flash_freq


def format_bootloader_path(path, flash_mode, flash_freq):
    return path.replace("$FLASH_MODE$", flash_mode).replace("$FLASH_FREQ$", flash_freq)


def detect_chip(port):
    """Detect ESP chip type."""
    try:
        chip = esptool.ESPLoader.detect_chip(port)
        chip.connect()
        return chip
    except esptool.FatalError as err:
        raise Esp_flasherError(f"ESP Chip Auto-Detection failed: {err}") from err

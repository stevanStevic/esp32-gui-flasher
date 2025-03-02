from esp_flasher.core.chip_utils import detect_chip, read_chip_info


def dump_info(port):
    try:
        chip = detect_chip(port)
        info = read_chip_info(chip)

        print("\nChip Information:")
        print(f" - Chip Family: {info.family}")
        print(f" - Model: {info.model}")
        print(f" - Cores: {info.num_cores}")
        print(f" - CPU Frequency: {info.cpu_frequency}")
        print(f" - Bluetooth: {'YES' if info.has_bluetooth else 'NO'}")
        print(f" - Embedded Flash: {'YES' if info.has_embedded_flash else 'NO'}")
        print(
            f" - Factory-Calibrated ADC: {'YES' if info.has_factory_calibrated_adc else 'NO'}"
        )
        print(f" - MAC Address: {info.mac}")
        chip._port.close()

        return info
    except Exception as e:
        print(f"Error retrieving chip info: {str(e)}")

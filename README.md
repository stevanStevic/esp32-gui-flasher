
# ESP32 GUI Flasher with Connection to Thermal Printer

ESP32 GUI Flasher is an app for ESP8266 / ESP32 designed to make flashing your firmware easy with ability to print device info onto connected thermal printer.

 * Pre-built binary for Windows.
 * Using your firmware release as a zip file.
 * Hiding all non-essential options for flashing.
 * All necessary options are set automatically.
 * Provides optional connection to thermal printer.

The flashing process is done using [esptool](https://github.com/espressif/esptool) from espressif.

## Instructions 

Click `Browse` under `Firmware` and select a zipped ESP-IDF release. The .zip file must contain a flasher_args.json file, as well as all relevant files used for flashing like application binary, partitions, bootloader and any other optional files like spiffs storage or others. 

## Installation

- Check the releases section for released binary.
- Download and double-click and it'll start.

In the odd case of your antivirus going haywire over that application, it's a [false positive.](https://github.com/pyinstaller/pyinstaller/issues/3802)

## Build it yourself

If you want to build this application yourself you need to:

- Install Python 3.x
- Create virtual env `python -m venv .venv` and activate it with `.\.venv\Scripts\activate` for Windows.
- Download this project and run `pip3 install -e .` in the project's root.
- Start the GUI using `esp_flasher`. Alternatively, you can use the command line interface (
  type `esp_flasher -h` for info)
- (Optional) Build the executable with these [instructions](./build-instructions.md).

## Acknowledgments

This project is based on the work from:
- [ESP_Flasher](https://github.com/Jason2866/ESP_Flasher/tree/factory)
- [esphome-flasher](https://github.com/esphome/esphome-flasher/tree/main)

Many thanks to the contributors of those project.

## License

[MIT](http://opensource.org/licenses/MIT)
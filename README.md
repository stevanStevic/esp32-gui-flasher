
# ESP32 GUI Flasher with Connection to Thermal Printer

ESP32 GUI Flasher is an app for ESP8266 / ESP32 designed to make flashing your firmware easy with ability to print device info onto connected thermal printer.

 * Pre-built binary for Windows.
 * Hiding all non-essential options for flashing.
 * All necessary options are set automatically.
 * Provides optional connection to thermal printer.

The flashing process is done using [esptool](https://github.com/espressif/esptool) from espressif.

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

### Mac OSX (compiled binary only for 11 and newer)

Driver maybe needed for Mac OSx.

Info: https://www.silabs.com/community/interface/forum.topic.html/vcp_driver_for_macosbigsur110x-krlP

Driver: https://www.silabs.com/documents/public/software/Mac_OSX_VCP_Driver.zip

## License

[MIT](http://opensource.org/licenses/MIT)
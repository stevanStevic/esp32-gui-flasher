# macOS

`pyinstaller -F -w -n ESP32-Flasher -i icon.icns esp_flasher/__main__.py`

# Windows

1. `pip install -r requirements_build.txt`
1. Check with `python -m esp_flasher.__main__`
1. `python -m PyInstaller.__main__ -F -w -n ESP32-Flasher -i icon.ico esp_flasher\__main__.py`
1. Go to `dist` folder, check ESP32-Flasher.exe works.

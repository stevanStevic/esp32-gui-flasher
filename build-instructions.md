# Linux

`python3 -m PyInstaller -F --add-data "icon.png:." -n ESP32-Flasher -i icon.png esp_flasher/__main__.py`

# Windows

1. `pip install -r requirements_build.txt -r requirements.txt -r requirements_win.txt`
1. Check with `python -m esp_flasher.__main__`
1. `python -m PyInstaller.__main__ -F -w -n ESP32-Flasher -i icon.ico --hidden-import pywin32 esp_flasher\__main__.py`
1. Go to `dist` folder, check ESP32-Flasher.exe works.

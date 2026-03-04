import os
import sys
import warnings

from esp_flasher.cli.commands import parse_args
from esp_flasher.cli.logging import show_logs
from esp_flasher.core.flasher import run_esp_flasher
from esp_flasher.cli.chip_info import dump_info
from esp_flasher.helpers.serial_utils import select_port
from PyQt5.QtWidgets import QMessageBox


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


def launch_gui(module_paths=None):
    from esp_flasher.gui.main_window import MainWindow
    from PyQt5.QtWidgets import QApplication

    if module_paths is None:
        module_paths = []

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    main_window = MainWindow(module_paths=module_paths)
    main_window.show()
    sys.exit(app.exec_())


def _resolve_builtin_printing_module() -> str:
    """Return the absolute path to the built-in registration/printing module."""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "modules",
        "registration_printing",
    )


def main():
    args = parse_args(sys.argv)

    if args.gui:
        try:
            module_paths = list(args.load_modules)

            # Handle deprecated --enable-device-registration-and-printing flag
            if args.enable_device_registration_and_printing:
                warnings.warn(
                    "--enable-device-registration-and-printing is deprecated. "
                    "Use '--load-module <path>' instead. See --help for details.",
                    DeprecationWarning,
                    stacklevel=1,
                )
                builtin_path = _resolve_builtin_printing_module()
                if builtin_path not in module_paths:
                    module_paths.append(builtin_path)

            launch_gui(module_paths=module_paths)
        except Exception as err:
            try:
                from esp_flasher.gui.main_window import show_popup
                show_popup("Error", f"An error occurred: {str(err)}", QMessageBox.Critical)
            except Exception:
                print(f"An error occurred: {str(err)}")
            return 1
        except KeyboardInterrupt:
            return 1
    else:
        try:
            return run(sys.argv)
        except Exception as err:
            print(f"An error occurred: {str(err)}")
            return 1
        except KeyboardInterrupt:
            return 1


if __name__ == "__main__":
    sys.exit(main())

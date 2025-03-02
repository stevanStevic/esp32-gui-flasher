import sys
from esp_flasher.cli.commands import parse_args
from esp_flasher.cli.logging import show_logs
from esp_flasher.core.flasher import run_esp_flasher
from esp_flasher.cli.chip_info import dump_info
from esp_flasher.helpers.serial_utils import select_port


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


def main():
    try:
        if len(sys.argv) <= 1:
            from esp_flasher.gui.main_window import MainWindow
            from PyQt5.QtWidgets import QApplication

            app = QApplication(sys.argv)
            app.setStyle("Fusion")
            main_window = MainWindow()
            main_window.show()
            sys.exit(app.exec_())
        else:
            return run(sys.argv)
    except Exception as err:
        print(f"Error: {str(err)}")
        return 1
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(main())

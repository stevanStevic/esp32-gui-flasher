import sys

from esp_flasher.cli.commands import parse_args


def launch_gui(module_paths=None):
    from esp_flasher.gui.main_window import MainWindow
    from PyQt5.QtWidgets import QApplication, QMessageBox

    if module_paths is None:
        module_paths = []

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    main_window = MainWindow(module_paths=module_paths)
    main_window.show()
    sys.exit(app.exec_())


_COMMAND_HANDLERS = {
    "info":  "esp_flasher.cli.handlers:handle_info",
    "flash": "esp_flasher.cli.handlers:handle_flash",
    "logs":  "esp_flasher.cli.handlers:handle_logs",
    "test":  "esp_flasher.cli.handlers:handle_test",
}


def _get_handler(command):
    """Lazily import and return the handler for *command*."""
    entry = _COMMAND_HANDLERS[command]
    module_path, func_name = entry.split(":")
    from importlib import import_module
    mod = import_module(module_path)
    return getattr(mod, func_name)


def main():
    args = parse_args(sys.argv)

    # ── GUI mode ─────────────────────────────────────────────────────
    if args.gui:
        try:
            launch_gui(module_paths=list(args.load_modules))
        except KeyboardInterrupt:
            return 1
        except Exception as err:
            print(f"GUI error: {err}")
            return 1
        return 0

    # ── CLI subcommand mode ──────────────────────────────────────────
    if not args.command:
        parse_args(["--help"])  # prints help and exits

    try:
        handler = _get_handler(args.command)
        result = handler(args)
        # handle_test returns False on failure
        if result is False:
            return 1
    except KeyboardInterrupt:
        print()
        return 1
    except Exception as err:
        print(f"Error: {err}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Centralized application state shared across all GUI sections and modules."""


class AppState:
    """Holds shared data and UI callbacks so that GUI sections never reach
    into ``MainWindow`` internals.

    ``MainWindow`` creates *one* instance, wires up the callback attributes,
    and passes it to every section / module constructor.
    """

    def __init__(self):
        # ── Shared data ───────────────────────────────────────────────
        self.firmware = ""
        self.chip_port = ""
        self.mac_address = None
        self.device_name = ""
        self.test_module = None

        # ── Per-module storage (avoids hardcoding module fields) ──────
        self.module_data = {}

        # ── UI references (set by MainWindow after widget creation) ───
        self.console = None  # QTextEdit widget

        # ── UI callbacks (set by MainWindow) ──────────────────────────
        self.set_log_file = lambda path: None
        self.close_log_file = lambda: None
        self.show_error_popup = lambda msg: None
        self.show_success_popup = lambda msg: None
        self.show_testing_popup = lambda msg: None
        self.close_testing_popup = lambda: None

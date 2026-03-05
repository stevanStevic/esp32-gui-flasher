from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QGroupBox


class GUIModule(ABC):
    """Abstract base class for loadable GUI extension modules.

    Each module provides a QGroupBox section that is inserted into the main
    window layout between the Chip Info and Firmware sections.

    To create a module, subclass GUIModule, implement the required methods,
    and place the .py file anywhere on disk. Load it at startup with:
        --gui --load-module /path/to/my_module.py

    Example minimal module:

        from esp_flasher.gui.module_base import GUIModule
        from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QLabel

        class HelloModule(GUIModule):
            def get_name(self):
                return "Hello Module"

            def create_section(self, parent):
                box = QGroupBox("Hello")
                layout = QVBoxLayout()
                layout.addWidget(QLabel("Hello from a module!"))
                box.setLayout(layout)
                return box
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return a human-readable name for this module (used in logs)."""
        ...

    @abstractmethod
    def create_section(self, state) -> QGroupBox:
        """Build and return the QGroupBox widget for this module.

        Args:
            state: The :class:`~esp_flasher.gui.app_state.AppState` instance.
                   Use it to read/write shared application state such as
                   ``state.mac_address``, ``state.chip_port``,
                   ``state.firmware``, etc.  UI callbacks like
                   ``state.show_error_popup()`` are also available.

        Returns:
            A QGroupBox that will be added to the left panel of the GUI.
        """
        ...

    def apply_config(self, config: dict) -> None:
        """Called after ``create_section()`` with the loaded config dict.

        Override this to extract module-specific keys from the application
        config (``config.json``) and apply them to your section widgets.
        The default implementation is a no-op.

        Args:
            config: The full application configuration dictionary.
        """

    def dispose(self) -> None:
        """Cleanup hook called when the main window is closing.

        Override this to stop threads, release resources, or persist state.
        The default implementation is a no-op.
        """

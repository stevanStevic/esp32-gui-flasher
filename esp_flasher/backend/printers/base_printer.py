from abc import ABC, abstractmethod


class BasePrinter(ABC):
    """Abstract base class for printers."""

    @abstractmethod
    def print_label(self, message: str):
        """Prints a label with the given message."""
        pass

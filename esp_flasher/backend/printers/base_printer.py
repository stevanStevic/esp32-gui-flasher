from abc import ABC, abstractmethod


class BasePrinter(ABC):
    """Abstract base class for printers."""

    @abstractmethod
    def print_label(
        self,
        message: str,
        label_width: int,
        x_offset: int,
        y_offset: int,
        text_rotation: int,
        font_size: int,
    ):
        """Prints a label with the given message."""
        pass

"""Tests for esp_flasher.backend.printers.brother_printer module."""
from unittest.mock import patch, MagicMock, call

import pytest


class TestBrotherQLPrinter:
    """Tests for BrotherQLPrinter class."""

    @patch("esp_flasher.backend.printers.brother_printer.send")
    @patch("esp_flasher.backend.printers.brother_printer.convert")
    @patch("esp_flasher.backend.printers.brother_printer.BrotherQLRaster")
    def test_print_label_success(self, mock_raster_cls, mock_convert, mock_send):
        """Successful print creates raster, converts, and sends."""
        from esp_flasher.backend.printers.brother_printer import BrotherQLPrinter

        mock_ql = MagicMock()
        mock_raster_cls.return_value = mock_ql
        mock_convert.return_value = b"instructions"

        printer = BrotherQLPrinter("Brother_QL-600")
        result = printer.print_label(
            "DEV_001",
            label_width=62,
            x_offset=150,
            y_offset=100,
            text_rotation=270,
            font_size=10,
        )

        assert result == "Print job sent successfully."
        mock_raster_cls.assert_called_once_with("QL-600B")
        mock_convert.assert_called_once_with(
            mock_ql,
            ["DEV_001"],
            label="62",
            rotate=270,
            threshold=150,
            dither=True,
            compress=False,
            dpi_600=False,
        )
        mock_send.assert_called_once_with(b"instructions", "Brother_QL-600")

    @patch("esp_flasher.backend.printers.brother_printer.send")
    @patch("esp_flasher.backend.printers.brother_printer.convert")
    @patch("esp_flasher.backend.printers.brother_printer.BrotherQLRaster")
    def test_print_label_default_params(self, mock_raster_cls, mock_convert, mock_send):
        """Default parameters are passed correctly to convert."""
        from esp_flasher.backend.printers.brother_printer import BrotherQLPrinter

        mock_convert.return_value = b"instructions"

        printer = BrotherQLPrinter("test_printer")
        result = printer.print_label("Test Message")

        # Verify defaults
        mock_convert.assert_called_once()
        _, kwargs = mock_convert.call_args
        call_args = mock_convert.call_args
        # convert is called positional + keyword
        assert call_args[1]["label"] == "62"
        assert call_args[1]["rotate"] == 270
        assert call_args[1]["threshold"] == 100

    @patch("esp_flasher.backend.printers.brother_printer.send")
    @patch("esp_flasher.backend.printers.brother_printer.convert")
    @patch("esp_flasher.backend.printers.brother_printer.BrotherQLRaster")
    def test_print_label_error(self, mock_raster_cls, mock_convert, mock_send):
        """Error during printing returns error message string."""
        from esp_flasher.backend.printers.brother_printer import BrotherQLPrinter

        mock_convert.side_effect = RuntimeError("Printer offline")

        printer = BrotherQLPrinter("Brother_QL-600")
        result = printer.print_label("DEV_001")

        assert "Error printing label" in result
        assert "Printer offline" in result

    def test_inherits_base_printer(self):
        """BrotherQLPrinter should inherit from BasePrinter."""
        from esp_flasher.backend.printers.base_printer import BasePrinter
        from esp_flasher.backend.printers.brother_printer import BrotherQLPrinter

        assert issubclass(BrotherQLPrinter, BasePrinter)

    @patch("esp_flasher.backend.printers.brother_printer.send")
    @patch("esp_flasher.backend.printers.brother_printer.convert")
    @patch("esp_flasher.backend.printers.brother_printer.BrotherQLRaster")
    def test_printer_name_stored(self, mock_raster_cls, mock_convert, mock_send):
        """Printer name is stored as instance attribute."""
        from esp_flasher.backend.printers.brother_printer import BrotherQLPrinter

        printer = BrotherQLPrinter("usb://0x04f9:0x20a7")
        assert printer.printer_name == "usb://0x04f9:0x20a7"


class TestBasePrinter:
    """Tests for BasePrinter ABC."""

    def test_cannot_instantiate(self):
        """BasePrinter cannot be instantiated directly."""
        from esp_flasher.backend.printers.base_printer import BasePrinter

        with pytest.raises(TypeError):
            BasePrinter()

    def test_requires_print_label(self):
        """Subclass must implement print_label."""
        from esp_flasher.backend.printers.base_printer import BasePrinter

        class IncompletePrinter(BasePrinter):
            pass

        with pytest.raises(TypeError):
            IncompletePrinter()

    def test_complete_subclass(self):
        """Subclass implementing print_label can be instantiated."""
        from esp_flasher.backend.printers.base_printer import BasePrinter

        class CompletePrinter(BasePrinter):
            def print_label(self, message, label_width, x_offset, y_offset, text_rotation, font_size):
                return "OK"

        printer = CompletePrinter()
        assert printer.print_label("test", 62, 100, 100, 270, 20) == "OK"

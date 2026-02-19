"""Tests for esp_flasher.threads.printing_thread module."""
from unittest.mock import patch, MagicMock

import pytest


class TestPrintingThread:
    """Tests for PrintingThread class."""

    @patch("esp_flasher.threads.printing_thread.QThread.__init__", return_value=None)
    def test_construction_defaults(self, mock_init):
        """Default parameters are stored correctly."""
        from esp_flasher.threads.printing_thread import PrintingThread

        thread = PrintingThread("Brother_QL-600", "DEV_001")

        assert thread.printer_name == "Brother_QL-600"
        assert thread.message == "DEV_001"
        assert thread.label_width == 62
        assert thread.x_offset == 100
        assert thread.y_offset == 100
        assert thread.text_rotation == 270
        assert thread.font == 20

    @patch("esp_flasher.threads.printing_thread.QThread.__init__", return_value=None)
    def test_construction_custom(self, mock_init):
        """Custom parameters are stored correctly."""
        from esp_flasher.threads.printing_thread import PrintingThread

        thread = PrintingThread(
            "HP_Printer",
            "Custom Label",
            label_width=50,
            x_offset=200,
            y_offset=150,
            text_rotation=90,
            font=14,
        )

        assert thread.printer_name == "HP_Printer"
        assert thread.message == "Custom Label"
        assert thread.label_width == 50
        assert thread.x_offset == 200
        assert thread.y_offset == 150
        assert thread.text_rotation == 90
        assert thread.font == 14

    @patch("esp_flasher.threads.printing_thread.QThread.__init__", return_value=None)
    @patch("esp_flasher.threads.printing_thread.get_printer")
    def test_run_success(self, mock_get_printer, mock_init):
        """Successful run calls get_printer and print_label with correct args."""
        from esp_flasher.threads.printing_thread import PrintingThread

        mock_printer = MagicMock()
        mock_printer.print_label.return_value = "Print job sent successfully."
        mock_get_printer.return_value = mock_printer

        thread = PrintingThread(
            "Brother_QL-600",
            "DEV_001",
            label_width=62,
            x_offset=150,
            y_offset=100,
            text_rotation=270,
            font=10,
        )
        thread.run()

        mock_get_printer.assert_called_once_with("Brother_QL-600")
        mock_printer.print_label.assert_called_once_with(
            "DEV_001",
            label_width=62,
            x_offset=150,
            y_offset=100,
            text_rotation=270,
            font_size=10,
        )

    @patch("esp_flasher.threads.printing_thread.QThread.__init__", return_value=None)
    @patch("esp_flasher.threads.printing_thread.get_printer")
    def test_run_error_logged(self, mock_get_printer, mock_init):
        """Errors during printing are logged, not raised."""
        from esp_flasher.threads.printing_thread import PrintingThread

        mock_get_printer.side_effect = ValueError("Unsupported OS")

        thread = PrintingThread("SomePrinter", "Label")

        # Should not raise
        thread.run()

    @patch("esp_flasher.threads.printing_thread.QThread.__init__", return_value=None)
    @patch("esp_flasher.threads.printing_thread.get_printer")
    def test_run_print_error_logged(self, mock_get_printer, mock_init):
        """Error from print_label is logged, not raised."""
        from esp_flasher.threads.printing_thread import PrintingThread

        mock_printer = MagicMock()
        mock_printer.print_label.side_effect = RuntimeError("Paper jam")
        mock_get_printer.return_value = mock_printer

        thread = PrintingThread("Brother_QL-600", "DEV_001")

        # Should not raise
        thread.run()

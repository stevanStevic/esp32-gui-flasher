"""Tests for CLI handlers (esp_flasher.cli.handlers)."""

from argparse import Namespace
from unittest.mock import patch, MagicMock, call

import pytest

from esp_flasher.core.errors import EspFlasherError


# ── handle_info ──────────────────────────────────────────────────────

class TestHandleInfo:
    @patch("esp_flasher.cli.handlers.get_chip_info")
    def test_returns_chip_info(self, mock_get):
        from esp_flasher.cli.handlers import handle_info

        mock_info = MagicMock()
        mock_info.family = "ESP32"
        mock_info.model = "ESP32-S3"
        mock_info.mac = "AA:BB:CC:DD:EE:FF"
        mock_info.num_cores = 2
        mock_info.cpu_frequency = "240MHz"
        mock_info.has_bluetooth = True
        mock_info.has_embedded_flash = False
        mock_info.has_factory_calibrated_adc = True
        mock_get.return_value = mock_info

        args = Namespace(port="/dev/ttyUSB0")
        result = handle_info(args)

        mock_get.assert_called_once_with("/dev/ttyUSB0")
        assert result is mock_info

    @patch("esp_flasher.cli.handlers.get_chip_info")
    def test_propagates_error(self, mock_get):
        from esp_flasher.cli.handlers import handle_info

        mock_get.side_effect = RuntimeError("read failed")

        args = Namespace(port="/dev/ttyUSB0")
        with pytest.raises(RuntimeError, match="read failed"):
            handle_info(args)


# ── handle_flash ─────────────────────────────────────────────────────

class TestHandleFlash:
    @patch("esp_flasher.cli.handlers.run_esp_flasher")
    def test_calls_run_esp_flasher(self, mock_run):
        from esp_flasher.cli.handlers import handle_flash

        args = Namespace(port="/dev/ttyUSB0", firmware="fw.zip", baud_rate=460800)
        handle_flash(args)

        mock_run.assert_called_once_with("/dev/ttyUSB0", "fw.zip", baud_rate=460800)

    @patch("esp_flasher.cli.handlers.run_esp_flasher")
    def test_propagates_flasher_error(self, mock_run):
        from esp_flasher.cli.handlers import handle_flash

        mock_run.side_effect = EspFlasherError("flash failed")
        args = Namespace(port="/dev/ttyUSB0", firmware="fw.zip", baud_rate=115200)

        with pytest.raises(EspFlasherError, match="flash failed"):
            handle_flash(args)


# ── handle_logs ──────────────────────────────────────────────────────

class TestHandleLogs:
    @patch("esp_flasher.cli.handlers.read_serial_lines")
    def test_reads_and_prints_logs(self, mock_read_lines, capsys):
        from esp_flasher.cli.handlers import handle_logs

        def _lines(*a, **kw):
            yield "Hello from ESP"
            raise KeyboardInterrupt

        mock_read_lines.side_effect = _lines

        args = Namespace(port="/dev/ttyUSB0")
        handle_logs(args)

        captured = capsys.readouterr()
        assert "Hello from ESP" in captured.out

    @patch("esp_flasher.cli.handlers.read_serial_lines")
    def test_serial_error_raises(self, mock_read_lines):
        from esp_flasher.cli.handlers import handle_logs

        mock_read_lines.side_effect = EspFlasherError("Serial error: port busy")

        args = Namespace(port="/dev/ttyUSB0")
        with pytest.raises(EspFlasherError, match="Serial error"):
            handle_logs(args)


# ── handle_test ──────────────────────────────────────────────────────

class TestHandleTest:
    @patch("esp_flasher.cli.handlers.read_serial_lines")
    @patch("esp_flasher.cli.handlers.run_esp_flasher")
    def test_pass_on_regex_match(self, mock_flash, mock_read_lines):
        from esp_flasher.cli.handlers import handle_test

        mock_read_lines.return_value = iter(["BOOT_OK: system ready"])

        args = Namespace(
            port="/dev/ttyUSB0",
            firmware="fw.zip",
            baud_rate=460800,
            regex="BOOT_OK",
            timeout=10,
        )
        result = handle_test(args)

        assert result is True
        mock_flash.assert_called_once_with("/dev/ttyUSB0", "fw.zip", baud_rate=460800)

    @patch("esp_flasher.cli.handlers.read_serial_lines")
    @patch("esp_flasher.cli.handlers.run_esp_flasher")
    def test_fail_on_timeout(self, mock_flash, mock_read_lines):
        from esp_flasher.cli.handlers import handle_test

        # Empty iterator — no lines to read
        mock_read_lines.return_value = iter([])

        args = Namespace(
            port="/dev/ttyUSB0",
            firmware="fw.zip",
            baud_rate=460800,
            regex="NEVER_MATCHES",
            timeout=10,
        )
        result = handle_test(args)

        assert result is False
        mock_flash.assert_called_once()

    @patch("esp_flasher.cli.handlers.run_esp_flasher")
    def test_flash_error_propagates(self, mock_flash):
        from esp_flasher.cli.handlers import handle_test

        mock_flash.side_effect = EspFlasherError("flash failed")

        args = Namespace(
            port="/dev/ttyUSB0",
            firmware="fw.zip",
            baud_rate=460800,
            regex="OK",
            timeout=10,
        )
        with pytest.raises(EspFlasherError, match="flash failed"):
            handle_test(args)

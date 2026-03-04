"""Tests for CLI handlers (esp_flasher.cli.handlers)."""

from argparse import Namespace
from unittest.mock import patch, MagicMock, call

import pytest

from esp_flasher.helpers.utils import Esp_flasherError


# ── handle_info ──────────────────────────────────────────────────────

class TestHandleInfo:
    @patch("esp_flasher.cli.handlers.read_chip_info")
    @patch("esp_flasher.cli.handlers.detect_chip")
    def test_returns_chip_info(self, mock_detect, mock_read):
        from esp_flasher.cli.handlers import handle_info

        mock_chip = MagicMock()
        mock_detect.return_value = mock_chip
        mock_info = MagicMock()
        mock_info.family = "ESP32"
        mock_info.model = "ESP32-S3"
        mock_info.mac = "AA:BB:CC:DD:EE:FF"
        mock_info.num_cores = 2
        mock_info.cpu_frequency = "240MHz"
        mock_info.has_bluetooth = True
        mock_info.has_embedded_flash = False
        mock_info.has_factory_calibrated_adc = True
        mock_read.return_value = mock_info

        args = Namespace(port="/dev/ttyUSB0")
        result = handle_info(args)

        mock_detect.assert_called_once_with("/dev/ttyUSB0")
        mock_read.assert_called_once_with(mock_chip)
        assert result is mock_info
        mock_chip._port.close.assert_called_once()

    @patch("esp_flasher.cli.handlers.read_chip_info")
    @patch("esp_flasher.cli.handlers.detect_chip")
    def test_closes_port_on_error(self, mock_detect, mock_read):
        from esp_flasher.cli.handlers import handle_info

        mock_chip = MagicMock()
        mock_detect.return_value = mock_chip
        mock_read.side_effect = RuntimeError("read failed")

        args = Namespace(port="/dev/ttyUSB0")
        with pytest.raises(RuntimeError, match="read failed"):
            handle_info(args)

        mock_chip._port.close.assert_called_once()


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

        mock_run.side_effect = Esp_flasherError("flash failed")
        args = Namespace(port="/dev/ttyUSB0", firmware="fw.zip", baud_rate=115200)

        with pytest.raises(Esp_flasherError, match="flash failed"):
            handle_flash(args)


# ── handle_logs ──────────────────────────────────────────────────────

class TestHandleLogs:
    @patch("esp_flasher.cli.handlers.serial.Serial")
    def test_reads_and_prints_logs(self, mock_serial_cls, capsys):
        from esp_flasher.cli.handlers import handle_logs

        mock_port = MagicMock()
        mock_serial_cls.return_value.__enter__ = MagicMock(return_value=mock_port)
        mock_serial_cls.return_value.__exit__ = MagicMock(return_value=False)

        # Simulate: first call has data, second raises KeyboardInterrupt
        mock_port.in_waiting = 1
        mock_port.readline.side_effect = [b"Hello from ESP\n", KeyboardInterrupt]

        args = Namespace(port="/dev/ttyUSB0")
        handle_logs(args)

        captured = capsys.readouterr()
        assert "Hello from ESP" in captured.out

    @patch("esp_flasher.cli.handlers.serial.Serial")
    def test_serial_error_raises(self, mock_serial_cls):
        from esp_flasher.cli.handlers import handle_logs
        import serial

        mock_serial_cls.return_value.__enter__ = MagicMock(
            side_effect=serial.SerialException("port busy")
        )
        mock_serial_cls.return_value.__exit__ = MagicMock(return_value=False)

        args = Namespace(port="/dev/ttyUSB0")
        with pytest.raises(Esp_flasherError, match="Serial error"):
            handle_logs(args)


# ── handle_test ──────────────────────────────────────────────────────

class TestHandleTest:
    @patch("esp_flasher.cli.handlers.serial.Serial")
    @patch("esp_flasher.cli.handlers.run_esp_flasher")
    def test_pass_on_regex_match(self, mock_flash, mock_serial_cls):
        from esp_flasher.cli.handlers import handle_test

        mock_port = MagicMock()
        mock_serial_cls.return_value.__enter__ = MagicMock(return_value=mock_port)
        mock_serial_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_port.in_waiting = 1
        mock_port.readline.return_value = b"BOOT_OK: system ready\n"

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

    @patch("esp_flasher.cli.handlers.time")
    @patch("esp_flasher.cli.handlers.serial.Serial")
    @patch("esp_flasher.cli.handlers.run_esp_flasher")
    def test_fail_on_timeout(self, mock_flash, mock_serial_cls, mock_time):
        from esp_flasher.cli.handlers import handle_test

        mock_port = MagicMock()
        mock_serial_cls.return_value.__enter__ = MagicMock(return_value=mock_port)
        mock_serial_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_port.in_waiting = 0

        # Simulate: first time() call for deadline, then time() > deadline
        mock_time.time.side_effect = [100.0, 200.0]
        mock_time.sleep = MagicMock()

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

    @patch("esp_flasher.cli.handlers.serial.Serial")
    @patch("esp_flasher.cli.handlers.run_esp_flasher")
    def test_flash_error_propagates(self, mock_flash, mock_serial_cls):
        from esp_flasher.cli.handlers import handle_test

        mock_flash.side_effect = Esp_flasherError("flash failed")

        args = Namespace(
            port="/dev/ttyUSB0",
            firmware="fw.zip",
            baud_rate=460800,
            regex="OK",
            timeout=10,
        )
        with pytest.raises(Esp_flasherError, match="flash failed"):
            handle_test(args)

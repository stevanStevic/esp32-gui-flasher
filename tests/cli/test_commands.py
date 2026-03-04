"""Tests for CLI argument parsing (esp_flasher.cli.commands)."""

import pytest

from esp_flasher.cli.commands import parse_args
from esp_flasher.core.const import DEFAULT_BAUD_RATE


# ── GUI flag ─────────────────────────────────────────────────────────

class TestGuiFlag:
    def test_gui_flag_sets_attribute(self):
        args = parse_args(["prog", "--gui"])
        assert args.gui is True

    def test_gui_with_load_modules(self):
        args = parse_args(["prog", "--gui", "--load-module", "a.py", "--load-module", "b.py"])
        assert args.gui is True
        assert args.load_modules == ["a.py", "b.py"]

    def test_no_gui_default(self):
        args = parse_args(["prog", "info", "-p", "/dev/ttyUSB0"])
        assert args.gui is False


# ── info ─────────────────────────────────────────────────────────────

class TestInfoCommand:
    def test_info_basic(self):
        args = parse_args(["prog", "info", "-p", "/dev/ttyUSB0"])
        assert args.command == "info"
        assert args.port == "/dev/ttyUSB0"

    def test_info_requires_port(self):
        with pytest.raises(SystemExit):
            parse_args(["prog", "info"])


# ── flash ────────────────────────────────────────────────────────────

class TestFlashCommand:
    def test_flash_basic(self):
        args = parse_args(["prog", "flash", "-p", "/dev/ttyUSB0", "--firmware", "fw.zip"])
        assert args.command == "flash"
        assert args.port == "/dev/ttyUSB0"
        assert args.firmware == "fw.zip"
        assert args.baud_rate == DEFAULT_BAUD_RATE

    def test_flash_custom_baud(self):
        args = parse_args(["prog", "flash", "-p", "/dev/ttyUSB0", "--firmware", "fw.zip", "--baud", "115200"])
        assert args.baud_rate == 115200

    def test_flash_requires_firmware(self):
        with pytest.raises(SystemExit):
            parse_args(["prog", "flash", "-p", "/dev/ttyUSB0"])

    def test_flash_requires_port(self):
        with pytest.raises(SystemExit):
            parse_args(["prog", "flash", "--firmware", "fw.zip"])


# ── logs ─────────────────────────────────────────────────────────────

class TestLogsCommand:
    def test_logs_basic(self):
        args = parse_args(["prog", "logs", "-p", "/dev/ttyUSB0"])
        assert args.command == "logs"
        assert args.port == "/dev/ttyUSB0"

    def test_logs_requires_port(self):
        with pytest.raises(SystemExit):
            parse_args(["prog", "logs"])


# ── test ─────────────────────────────────────────────────────────────

class TestTestCommand:
    def test_test_all_args(self):
        args = parse_args([
            "prog", "test",
            "-p", "/dev/ttyUSB0",
            "--firmware", "fw.zip",
            "--regex", "BOOT_OK",
            "--timeout", "30",
        ])
        assert args.command == "test"
        assert args.port == "/dev/ttyUSB0"
        assert args.firmware == "fw.zip"
        assert args.regex == "BOOT_OK"
        assert args.timeout == 30
        assert args.baud_rate == DEFAULT_BAUD_RATE

    def test_test_custom_baud(self):
        args = parse_args([
            "prog", "test",
            "-p", "/dev/ttyUSB0",
            "--firmware", "fw.zip",
            "--regex", "OK",
            "--timeout", "10",
            "--baud", "115200",
        ])
        assert args.baud_rate == 115200

    def test_test_requires_regex(self):
        with pytest.raises(SystemExit):
            parse_args(["prog", "test", "-p", "/dev/ttyUSB0", "--firmware", "fw.zip", "--timeout", "10"])

    def test_test_requires_timeout(self):
        with pytest.raises(SystemExit):
            parse_args(["prog", "test", "-p", "/dev/ttyUSB0", "--firmware", "fw.zip", "--regex", "OK"])

    def test_test_requires_firmware(self):
        with pytest.raises(SystemExit):
            parse_args(["prog", "test", "-p", "/dev/ttyUSB0", "--regex", "OK", "--timeout", "10"])


# ── no subcommand ────────────────────────────────────────────────────

class TestNoSubcommand:
    def test_no_command_sets_none(self):
        args = parse_args(["prog"])
        assert args.command is None
        assert args.gui is False

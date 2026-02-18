"""Tests for esp_flasher.helpers.utils module."""
import json
import os
from unittest.mock import patch

import pytest

from esp_flasher.helpers.utils import (
    Esp_flasherError,
    load_config,
    get_device_dir,
    get_flash_log_path,
    get_testing_log_path,
)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_success(self, tmp_path):
        """Valid JSON config is loaded correctly."""
        config_data = {"secure_boot": {"key": "value"}, "chip_port": "COM6"}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_data))

        result = load_config(str(config_path))
        assert result == config_data

    def test_load_file_not_found(self):
        """Non-existent config file raises Esp_flasherError."""
        with pytest.raises(Esp_flasherError, match="Config file.*not found"):
            load_config("/nonexistent/config.json")

    def test_load_invalid_json(self, tmp_path):
        """Invalid JSON raises Esp_flasherError."""
        config_path = tmp_path / "bad.json"
        config_path.write_text("{invalid json content")

        with pytest.raises(Esp_flasherError, match="Error parsing config file"):
            load_config(str(config_path))

    def test_load_empty_json(self, tmp_path):
        """Empty JSON object is valid."""
        config_path = tmp_path / "empty.json"
        config_path.write_text("{}")

        result = load_config(str(config_path))
        assert result == {}


class TestGetDeviceDir:
    """Tests for get_device_dir function."""

    def test_with_device_name(self, tmp_path, monkeypatch):
        """Creates directory named after the device."""
        monkeypatch.chdir(tmp_path)
        result = get_device_dir(device_name="MY_DEVICE")
        assert os.path.basename(result) == "MY_DEVICE"
        assert os.path.isdir(result)

    def test_with_mac_address(self, tmp_path, monkeypatch):
        """Creates directory with MAC address (colons replaced by underscores)."""
        monkeypatch.chdir(tmp_path)
        result = get_device_dir(mac_address="AA:BB:CC:DD:EE:FF")
        assert os.path.basename(result) == "AA_BB_CC_DD_EE_FF"
        assert os.path.isdir(result)

    def test_with_no_identifiers(self, tmp_path, monkeypatch):
        """Falls back to 'unknown' directory."""
        monkeypatch.chdir(tmp_path)
        result = get_device_dir()
        assert os.path.basename(result) == "unknown"
        assert os.path.isdir(result)

    def test_device_name_takes_priority(self, tmp_path, monkeypatch):
        """device_name is used over mac_address when both are provided."""
        monkeypatch.chdir(tmp_path)
        result = get_device_dir(device_name="DEV01", mac_address="AA:BB:CC:DD:EE:FF")
        assert os.path.basename(result) == "DEV01"


class TestLogPaths:
    """Tests for get_flash_log_path and get_testing_log_path."""

    def test_flash_log_path(self, tmp_path):
        result = get_flash_log_path(str(tmp_path))
        assert result.startswith(str(tmp_path))
        assert "flashing_" in result
        assert result.endswith(".log")

    def test_testing_log_path(self, tmp_path):
        result = get_testing_log_path(str(tmp_path))
        assert result.startswith(str(tmp_path))
        assert "testing_" in result
        assert result.endswith(".log")

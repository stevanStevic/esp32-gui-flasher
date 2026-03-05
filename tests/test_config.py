"""Tests for esp_flasher.config module."""
import json

import pytest

from esp_flasher.config import load_config
from esp_flasher.core.errors import EspFlasherError


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
        """Non-existent config file raises EspFlasherError."""
        with pytest.raises(EspFlasherError, match="Config file.*not found"):
            load_config("/nonexistent/config.json")

    def test_load_invalid_json(self, tmp_path):
        """Invalid JSON raises EspFlasherError."""
        config_path = tmp_path / "bad.json"
        config_path.write_text("{invalid json content")

        with pytest.raises(EspFlasherError, match="Error parsing config file"):
            load_config(str(config_path))

    def test_load_empty_json(self, tmp_path):
        """Empty JSON object is valid."""
        config_path = tmp_path / "empty.json"
        config_path.write_text("{}")

        result = load_config(str(config_path))
        assert result == {}

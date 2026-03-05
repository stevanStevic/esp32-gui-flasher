"""Tests for esp_flasher.model.test_module module."""
import pytest

from esp_flasher.model.test_module import DeviceTestModule


class TestTestModule:
    """Tests for DeviceTestModule class."""

    def test_initial_state(self):
        """Default state: count=0, not testing."""
        module = DeviceTestModule(
            regex="test_pattern",
            timeout_seconds=10,
        )
        assert module.successful_flash_count == 0
        assert module.is_testing is False
        assert module.test_enabled is False
        assert module.test_board_xth_occurrence == 0
        assert module.regex == "test_pattern"
        assert module.timeout_seconds == 10

    def test_increment_flash_count(self):
        """increment_flash_count increases the counter."""
        module = DeviceTestModule(regex="", timeout_seconds=5)
        module.increment_flash_count()
        module.increment_flash_count()
        module.increment_flash_count()
        assert module.successful_flash_count == 3

    def test_should_run_test_disabled(self):
        """When test_enabled is False, should_run_test always returns False."""
        module = DeviceTestModule(
            regex="pattern",
            timeout_seconds=10,
            test_enabled=False,
            test_board_xth_occurrence=2,
        )
        module.increment_flash_count()
        module.increment_flash_count()
        assert module.should_run_test() is False

    def test_should_run_test_every_nth(self):
        """should_run_test returns True only every Nth flash."""
        module = DeviceTestModule(
            regex="pattern",
            timeout_seconds=10,
            test_enabled=True,
            test_board_xth_occurrence=3,
        )
        # Count 0: 0 % 3 == 0 → True (edge case: initial state)
        assert module.should_run_test() is True

        module.increment_flash_count()  # count=1
        assert module.should_run_test() is False

        module.increment_flash_count()  # count=2
        assert module.should_run_test() is False

        module.increment_flash_count()  # count=3
        assert module.should_run_test() is True

        module.increment_flash_count()  # count=4
        assert module.should_run_test() is False

        module.increment_flash_count()  # count=5
        assert module.should_run_test() is False

        module.increment_flash_count()  # count=6
        assert module.should_run_test() is True

    def test_should_run_test_zero_occurrence(self):
        """When test_board_xth_occurrence is 0, should never run (avoid ZeroDivisionError)."""
        module = DeviceTestModule(
            regex="pattern",
            timeout_seconds=10,
            test_enabled=True,
            test_board_xth_occurrence=0,
        )
        module.increment_flash_count()
        # xth_occurrence > 0 is False, so should_run_test returns False
        assert module.should_run_test() is False

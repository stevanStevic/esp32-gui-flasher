"""Tests for esp_flasher.gui.threads.test_thread (TestThread logic)."""
from unittest.mock import MagicMock, patch

import pytest

from esp_flasher.model.test_module import DeviceTestModule


class TestTestThreadLogic:
    """Test the process_log_line logic from TestThread without requiring Qt event loop.

    We import TestThread and test its log processing method with mocked signals.
    """

    @patch("esp_flasher.gui.threads.test_thread.QTimer")
    @patch("esp_flasher.gui.threads.test_thread.QObject.__init__", return_value=None)
    def test_process_log_line_match(self, mock_qobj_init, mock_qtimer):
        """Matching log line should stop test and emit success signal."""
        from esp_flasher.gui.threads.test_thread import TestThread

        model = DeviceTestModule(
            regex=r"Multicore\s+app",
            timeout_seconds=10,
            test_enabled=True,
            test_board_xth_occurrence=1,
        )
        model.is_testing = True

        thread = TestThread(model)
        thread.test_success_signal = MagicMock()
        thread.test_stopped_signal = MagicMock()
        thread._timer = MagicMock()

        thread.process_log_line("Boot complete: Multicore app started")

        assert model.is_testing is False
        thread.test_success_signal.emit.assert_called_once_with("Device testing passed!")

    @patch("esp_flasher.gui.threads.test_thread.QTimer")
    @patch("esp_flasher.gui.threads.test_thread.QObject.__init__", return_value=None)
    def test_process_log_line_no_match(self, mock_qobj_init, mock_qtimer):
        """Non-matching log line should NOT stop the test."""
        from esp_flasher.gui.threads.test_thread import TestThread

        model = DeviceTestModule(
            regex=r"Multicore\s+app",
            timeout_seconds=10,
            test_enabled=True,
            test_board_xth_occurrence=1,
        )
        model.is_testing = True

        thread = TestThread(model)
        thread.test_success_signal = MagicMock()
        thread._timer = MagicMock()

        thread.process_log_line("Some unrelated log line")

        assert model.is_testing is True
        thread.test_success_signal.emit.assert_not_called()

    @patch("esp_flasher.gui.threads.test_thread.QTimer")
    @patch("esp_flasher.gui.threads.test_thread.QObject.__init__", return_value=None)
    def test_process_log_line_not_testing(self, mock_qobj_init, mock_qtimer):
        """When not testing, matching line should be ignored."""
        from esp_flasher.gui.threads.test_thread import TestThread

        model = DeviceTestModule(
            regex=r"Multicore\s+app",
            timeout_seconds=10,
        )
        model.is_testing = False

        thread = TestThread(model)
        thread.test_success_signal = MagicMock()
        thread._timer = MagicMock()

        thread.process_log_line("Multicore app started")

        thread.test_success_signal.emit.assert_not_called()

    @patch("esp_flasher.gui.threads.test_thread.QTimer")
    @patch("esp_flasher.gui.threads.test_thread.QObject.__init__", return_value=None)
    def test_on_timeout(self, mock_qobj_init, mock_qtimer):
        """Timeout while testing should emit failure signal."""
        from esp_flasher.gui.threads.test_thread import TestThread

        model = DeviceTestModule(
            regex=r"test",
            timeout_seconds=5,
            test_enabled=True,
        )
        model.is_testing = True

        thread = TestThread(model)
        thread.test_timeout_signal = MagicMock()
        thread.test_stopped_signal = MagicMock()
        thread._timer = MagicMock()

        thread._on_timeout()

        assert model.is_testing is False
        thread.test_timeout_signal.emit.assert_called_once_with("Device testing failed!")

"""Tests for esp_flasher.backend.api_client module."""
from unittest.mock import patch, MagicMock

import pytest

from esp_flasher.backend.api_client import publish_mac_address


class TestPublishMacAddress:
    """Tests for publish_mac_address function."""

    @patch("esp_flasher.backend.api_client.requests.Session")
    def test_success_201(self, mock_session_cls):
        """201 response with device_name returns (name, None)."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"device_name": "DEV_001"}
        mock_response.raise_for_status.return_value = None

        mock_session = MagicMock()
        mock_session.post.return_value = mock_response
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_cls.return_value = mock_session

        name, error = publish_mac_address(
            "http://localhost:5000/publish", "KEY", "SECRET", "AA:BB:CC:DD:EE:FF"
        )

        assert name == "DEV_001"
        assert error is None

        # Verify correct headers and payload
        call_kwargs = mock_session.post.call_args
        assert call_kwargs[0][0] == "http://localhost:5000/publish"
        headers = call_kwargs[1]["headers"] if "headers" in call_kwargs[1] else call_kwargs[1].get("headers")
        assert headers["X-API-KEY"] == "KEY"
        assert headers["X-API-SECRET"] == "SECRET"
        assert headers["Content-Type"] == "application/json"
        payload = call_kwargs[1]["json"]
        assert payload["mac_address"] == "AA:BB:CC:DD:EE:FF"

    @patch("esp_flasher.backend.api_client.requests.Session")
    def test_http_error(self, mock_session_cls):
        """HTTP error returns (None, error_message)."""
        from requests.exceptions import HTTPError

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.json.return_value = {"message": "Invalid MAC format"}

        http_error = HTTPError(response=mock_response)
        mock_response.raise_for_status.side_effect = http_error

        mock_session = MagicMock()
        mock_session.post.return_value = mock_response
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_cls.return_value = mock_session

        name, error = publish_mac_address(
            "http://localhost:5000/publish", "KEY", "SECRET", "INVALID"
        )

        assert name is None
        assert "HTTP error" in error
        assert "400" in error

    @patch("esp_flasher.backend.api_client.requests.Session")
    def test_connection_error(self, mock_session_cls):
        """Connection error returns (None, error_message)."""
        from requests.exceptions import ConnectionError as ReqConnectionError

        mock_session = MagicMock()
        mock_session.post.side_effect = ReqConnectionError("Connection refused")
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_cls.return_value = mock_session

        name, error = publish_mac_address(
            "http://localhost:5000/publish", "KEY", "SECRET", "AA:BB:CC:DD:EE:FF"
        )

        assert name is None
        assert "Request failed" in error

    @patch("esp_flasher.backend.api_client.requests.Session")
    def test_unexpected_error(self, mock_session_cls):
        """Unexpected exception returns (None, error_message)."""
        mock_session = MagicMock()
        mock_session.post.side_effect = ValueError("something weird")
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_cls.return_value = mock_session

        name, error = publish_mac_address(
            "http://localhost:5000/publish", "KEY", "SECRET", "AA:BB:CC:DD:EE:FF"
        )

        assert name is None
        assert "unexpected error" in error.lower()

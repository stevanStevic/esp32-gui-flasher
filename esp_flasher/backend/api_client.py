import requests
from requests.exceptions import RequestException, HTTPError


def publish_mac_address(
    api_endpoint: str, api_key: str, api_secret: str, mac_address: str
):
    """Send MAC address to the API endpoint with authentication."""
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
        "X-API-SECRET": api_secret,
    }
    payload = {"mac_address": mac_address}

    try:
        with requests.Session() as session:
            response = session.post(api_endpoint, headers=headers, json=payload)
            response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses

            if response.status_code == 201:
                return response.json().get("device_name", "Unknown Device"), None

            return (
                None,
                f"Unexpected status code: {response.status_code} {response.reason} - {response_data["message"]}",
            )

    except HTTPError as http_err:
        response_data = http_err.response.json()

        return (
            None,
            f"HTTP error: {response.status_code} {response.reason} - {response_data["message"]}",
        )
    except RequestException as req_err:
        return None, f"Request failed: {req_err}"
    except Exception as err:
        return None, f"An unexpected error occurred: {err}"

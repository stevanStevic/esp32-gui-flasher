import requests


def publish_mac_address(api_endpoint, api_key, api_secret, mac_address):
    """Send MAC address to API endpoint with authentication."""
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
        "X-API-SECRET": api_secret,
    }

    payload = {"mac_address": mac_address}

    try:
        response = requests.post(api_endpoint, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception if HTTP error occurs

        response_data = response.json()

        if response_data.get("status") == "success":
            return response_data.get("device_name", "Unknown Device"), None  # Success
        return (
            None,
            f"API Error: {response_data.get('message', 'Unknown error from server')}",
        )

    except requests.exceptions.RequestException as e:
        return None, f"Network Error: {e}"

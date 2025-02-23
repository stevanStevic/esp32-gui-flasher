import requests
import json


def publish_mac_address(api_endpoint, api_key, api_secret, mac_address):
    """Send MAC address to API endpoint with authentication."""
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key,
        "X-API-SECRET": api_secret,
    }

    payload = {"mac_address": mac_address}

    print("Publishing", headers)
    print("Payload", payload)

    try:
        response = requests.post(api_endpoint, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception if HTTP error occurs

        response_data = response.json()

        if response_data.get("status") == "success":
            device_name = response_data.get("device_name", "Unknown Device")
            return device_name, None  # Success case

        error_message = response_data.get("message", "Unknown error from server")
        return None, f"API Error: {error_message}"

    except requests.exceptions.RequestException as e:
        return None, f"Network Error: {e}"


# # Example MAC address to send
# if __name__ == "__main__":
#     test_mac = "AA:BB:CC:DD:EE:FF"
#     publish_mac_address(test_mac)

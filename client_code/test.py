import requests

try:
    response = requests.post("https://localhost:8081", data={})
    response.raise_for_status()  # Raises HTTPError for bad responses
    print(response.json())
except requests.exceptions.ConnectionError as e:
    print(f"Connection error: {e}")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
except requests.exceptions.SSLError as e:
    print(f"SSL error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

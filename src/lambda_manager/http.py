import requests


DEFAULT_TIMEOUT_SECONDS = 30


def send_json_request(request: requests.Request) -> dict:
    with requests.Session() as session:
        response = session.send(request.prepare(), timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()

import base64
import json
import os
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://cloud.lambda.ai/api/v1"
USER_AGENT = "lambda-manager/0.1"


def build_request(api_key: str, base_url: str) -> Request:
    token = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("ascii")
    return Request(
        f"{base_url.rstrip('/')}/instance-types",
        headers={
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )


def fetch_instance_types(
    api_key: str | None = None, base_url: str | None = None
) -> dict:
    resolved_api_key = api_key or os.environ["LAMBDA_API_KEY"]
    resolved_base_url = (base_url or os.environ.get("LAMBDA_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    request = build_request(resolved_api_key, resolved_base_url)

    with urlopen(request) as response:
        return json.load(response)

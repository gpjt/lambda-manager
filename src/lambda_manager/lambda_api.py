import base64
import os
import requests


DEFAULT_BASE_URL = "https://cloud.lambda.ai/api/v1"
USER_AGENT = "lambda-manager/0.1"
DEFAULT_TIMEOUT_SECONDS = 30


def _auth_headers(api_key: str) -> dict:
    token = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("ascii")
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }


def build_instance_types_request(api_key: str, base_url: str) -> requests.Request:
    return requests.Request(
        method="GET",
        url=f"{base_url.rstrip('/')}/instance-types",
        headers=_auth_headers(api_key),
    )


def build_launch_request(
    api_key: str,
    base_url: str,
    region_name: str,
    instance_type_name: str,
    ssh_key_name: str,
) -> requests.Request:
    return requests.Request(
        method="POST",
        url=f"{base_url.rstrip('/')}/instance-operations/launch",
        json={
            "region_name": region_name,
            "instance_type_name": instance_type_name,
            "ssh_key_names": [ssh_key_name],
        },
        headers=_auth_headers(api_key),
    )


def available_region_names(payload: dict, instance_type_name: str) -> list[str]:
    instance_type = payload.get("data", {}).get(instance_type_name, {})
    regions = instance_type.get("regions_with_capacity_available", [])
    return [region["name"] for region in regions]


def fetch_instance_types(
    api_key: str | None = None, base_url: str | None = None
) -> dict:
    resolved_api_key = api_key or os.environ["LAMBDA_API_KEY"]
    resolved_base_url = (base_url or os.environ.get("LAMBDA_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    request = build_instance_types_request(resolved_api_key, resolved_base_url)

    with requests.Session() as session:
        response = session.send(request.prepare(), timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()


def launch_instance(
    *,
    region_name: str,
    instance_type_name: str,
    ssh_key_name: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict:
    resolved_api_key = api_key or os.environ["LAMBDA_API_KEY"]
    resolved_base_url = (base_url or os.environ.get("LAMBDA_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    request = build_launch_request(
        resolved_api_key,
        resolved_base_url,
        region_name,
        instance_type_name,
        ssh_key_name,
    )

    with requests.Session() as session:
        response = session.send(request.prepare(), timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()

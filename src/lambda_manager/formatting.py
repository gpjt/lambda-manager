from datetime import datetime
import re

import requests

from lambda_manager.instance_types import available_instance_type_names
from lambda_manager.lambda_api import available_region_names


MAX_LOGGED_RESPONSE_BODY_LENGTH = 200


def print_status(message: str) -> None:
    print(f"{datetime.now().isoformat(timespec='seconds')} {message}", flush=True)


def _compact_response_body(body: str) -> str:
    compact = re.sub(r"\s+", " ", body).strip()
    if len(compact) > MAX_LOGGED_RESPONSE_BODY_LENGTH:
        return compact[: MAX_LOGGED_RESPONSE_BODY_LENGTH - 3] + "..."
    return compact


def format_request_exception(exc: requests.RequestException) -> str:
    message = str(exc)
    response = getattr(exc, "response", None)
    body = getattr(response, "text", None)
    if body:
        return f"{message} | body: {_compact_response_body(body)}"
    return message


def format_available_instance_types_status(payload: dict) -> str:
    available_names = available_instance_type_names(payload)
    if not available_names:
        return "Available instance types: none"

    parts = []
    for instance_type_name in available_names:
        regions = available_region_names(payload, instance_type_name)
        parts.append(f"{instance_type_name} (regions: {', '.join(regions)})")

    return "Available instance types: " + ", ".join(parts)


def format_instance_type_description_table(rows: list[tuple[str, str]]) -> str:
    description_width = max(
        len("description"), *(len(description) for description, _ in rows)
    )
    lines = [f"{'description'.ljust(description_width)}  name"]
    for description, name in rows:
        lines.append(f"{description.ljust(description_width)}  {name}")
    return "\n".join(lines)

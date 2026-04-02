import argparse
import os
import time
from datetime import datetime

import requests

from lambda_manager.dotenv import load_dotenv
from lambda_manager.instance_types import (
    available_instance_type_names,
    instance_type_description_rows,
)
from lambda_manager.lambda_api import (
    available_region_names,
    fetch_instance_types,
    launch_instance,
)
from lambda_manager.telegram import send_message


def print_status(message: str) -> None:
    print(f"{datetime.now().isoformat(timespec='seconds')} {message}", flush=True)


def format_request_exception(exc: requests.RequestException) -> str:
    message = str(exc)
    response = getattr(exc, "response", None)
    body = getattr(response, "text", None)
    if body:
        return f"{message} | body: {body}"
    return message


def format_available_instance_types_status(payload: dict) -> str:
    available_names = available_instance_type_names(payload)
    if not available_names:
        return "Available instance types: none"

    parts = []
    for instance_type_name in available_names:
        regions = available_region_names(payload, instance_type_name)
        parts.append(
            f"{instance_type_name} (regions: {', '.join(regions)})"
        )

    return "Available instance types: " + ", ".join(parts)


def format_instance_type_description_table(
    rows: list[tuple[str, str]],
) -> str:
    description_width = max(len("description"), *(len(description) for description, _ in rows))
    lines = [f"{'description'.ljust(description_width)}  name"]
    for description, name in rows:
        lines.append(f"{description.ljust(description_width)}  {name}")
    return "\n".join(lines)


def call_with_retries(
    label: str,
    operation,
    *,
    max_consecutive_failures: int,
    retry_delay_seconds: float,
    retryable_exception=None,
):
    consecutive_failures = 0
    while True:
        try:
            return operation()
        except requests.RequestException as exc:
            if retryable_exception is not None and not retryable_exception(exc):
                consecutive_failures += 1
                print_status(
                    f"{label} failed (attempt {consecutive_failures}/{max_consecutive_failures}): {format_request_exception(exc)}"
                )
                return None
            consecutive_failures += 1
            print_status(
                f"{label} failed (attempt {consecutive_failures}/{max_consecutive_failures}): {format_request_exception(exc)}"
            )
            if consecutive_failures >= max_consecutive_failures:
                return None
            time.sleep(retry_delay_seconds)


def is_retryable_launch_exception(exc: requests.RequestException) -> bool:
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code >= 500
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lambda_manager")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "list-instance-types",
        help="List Lambda Labs instance types that currently have launch capacity",
    )
    subparsers.add_parser(
        "list-instance-type-descriptions",
        help="List instance type descriptions together with their Lambda API names",
    )
    launch_parser = subparsers.add_parser(
        "launch-when-available",
        help="Poll until a requested instance type has capacity, then launch and notify",
    )
    launch_parser.add_argument("instance_type_name")
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)

    if args.command == "list-instance-types":
        payload = fetch_instance_types()
        for instance_type_name in available_instance_type_names(payload):
            print(instance_type_name)
        return 0

    if args.command == "list-instance-type-descriptions":
        payload = fetch_instance_types()
        print(format_instance_type_description_table(instance_type_description_rows(payload)))
        return 0

    if args.command == "launch-when-available":
        poll_interval_seconds = float(
            os.environ.get("LAMBDA_MANAGER_POLL_INTERVAL_SECONDS", "60")
        )
        max_polls = int(os.environ.get("LAMBDA_MANAGER_MAX_POLLS", "0"))
        retry_delay_seconds = float(
            os.environ.get("LAMBDA_MANAGER_RETRY_DELAY_SECONDS", "1")
        )
        max_consecutive_failures = int(
            os.environ.get("LAMBDA_MANAGER_MAX_CONSECUTIVE_FAILURES", "10")
        )
        ssh_key_name = os.environ["LAMBDA_SSH_KEY_NAME"]
        chat_id = os.environ["TELEGRAM_CHAT_ID"]
        poll_count = 0

        while True:
            poll_count += 1
            payload = call_with_retries(
                "Lambda API",
                fetch_instance_types,
                max_consecutive_failures=max_consecutive_failures,
                retry_delay_seconds=retry_delay_seconds,
            )
            if payload is None:
                return 1
            requested_regions = available_region_names(payload, args.instance_type_name)
            print_status(format_available_instance_types_status(payload))
            if requested_regions:
                for region_name in requested_regions:
                    launch_response = call_with_retries(
                        f"Lambda launch in {region_name}",
                        lambda region_name=region_name: launch_instance(
                            region_name=region_name,
                            instance_type_name=args.instance_type_name,
                            ssh_key_name=ssh_key_name,
                        ),
                        max_consecutive_failures=max_consecutive_failures,
                        retry_delay_seconds=retry_delay_seconds,
                        retryable_exception=is_retryable_launch_exception,
                    )
                    if launch_response is None:
                        continue
                    instance_id = launch_response["data"]["instance_ids"][0]
                    message = (
                        f"Launched {args.instance_type_name} in {region_name} as {instance_id}"
                    )
                    print_status(message)
                    notification_response = call_with_retries(
                        "Telegram API",
                        lambda: send_message(chat_id=chat_id, text=message),
                        max_consecutive_failures=max_consecutive_failures,
                        retry_delay_seconds=retry_delay_seconds,
                    )
                    if notification_response is None:
                        return 1
                    print_status("Telegram notification sent")
                    return 0
            if max_polls and poll_count >= max_polls:
                return 0
            time.sleep(poll_interval_seconds)

    return 1

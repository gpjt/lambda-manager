import argparse
import os
import time
from datetime import datetime

import requests

from lambda_manager.dotenv import load_dotenv
from lambda_manager.instance_types import available_instance_type_names
from lambda_manager.lambda_api import (
    fetch_instance_types,
    first_available_region_name,
    launch_instance,
)
from lambda_manager.telegram import send_message


def print_status(message: str) -> None:
    print(f"{datetime.now().isoformat(timespec='seconds')} {message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lambda_manager")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "list-instance-types",
        help="List Lambda Labs instance types that currently have launch capacity",
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

    if args.command == "launch-when-available":
        poll_interval_seconds = float(
            os.environ.get("LAMBDA_MANAGER_POLL_INTERVAL_SECONDS", "60")
        )
        ssh_key_name = os.environ["LAMBDA_SSH_KEY_NAME"]
        chat_id = os.environ["TELEGRAM_CHAT_ID"]

        while True:
            payload = fetch_instance_types()
            available_names = available_instance_type_names(payload)
            print_status(
                "Available instance types: "
                + (", ".join(available_names) if available_names else "none")
            )
            region_name = first_available_region_name(payload, args.instance_type_name)
            if region_name:
                launch_response = launch_instance(
                    region_name=region_name,
                    instance_type_name=args.instance_type_name,
                    ssh_key_name=ssh_key_name,
                )
                instance_id = launch_response["data"]["instance_ids"][0]
                message = (
                    f"Launched {args.instance_type_name} in {region_name} as {instance_id}"
                )
                print_status(message)
                try:
                    send_message(chat_id=chat_id, text=message)
                except requests.RequestException as exc:
                    print_status(
                        f"Telegram notification failed after launch: {exc}"
                    )
                return 0
            time.sleep(poll_interval_seconds)

    return 1

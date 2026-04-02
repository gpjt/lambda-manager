import os
import time

from lambda_manager.formatting import (
    format_available_instance_types_status,
    print_status,
)
from lambda_manager.lambda_api import (
    available_region_names,
    fetch_instance_types,
    launch_instance,
)
from lambda_manager.retry import call_with_retries, is_retryable_launch_exception
from lambda_manager.telegram import send_message


def handle_launch_when_available(instance_type_name: str) -> int:
    poll_interval_seconds = float(
        os.environ.get("LAMBDA_MANAGER_POLL_INTERVAL_SECONDS", "60")
    )
    max_polls = int(os.environ.get("LAMBDA_MANAGER_TEST_MAX_POLLS", "0"))
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
        requested_regions = available_region_names(payload, instance_type_name)
        print_status(format_available_instance_types_status(payload))
        if requested_regions:
            for region_name in requested_regions:
                launch_response = call_with_retries(
                    f"Lambda launch in {region_name}",
                    lambda region_name=region_name: launch_instance(
                        region_name=region_name,
                        instance_type_name=instance_type_name,
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
                    f"Launched {instance_type_name} in {region_name} as {instance_id}"
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

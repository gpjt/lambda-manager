import time

import requests

from lambda_manager.formatting import format_request_exception, print_status


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

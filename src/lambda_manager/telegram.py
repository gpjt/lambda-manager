import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_TELEGRAM_API_BASE_URL = "https://api.telegram.org"


def build_send_message_request(
    *,
    bot_token: str,
    chat_id: str,
    text: str,
    base_url: str,
) -> Request:
    body = urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    return Request(
        f"{base_url.rstrip('/')}/bot{bot_token}/sendMessage",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )


def send_message(
    *,
    chat_id: str,
    text: str,
    bot_token: str | None = None,
    base_url: str | None = None,
) -> dict:
    resolved_bot_token = bot_token or os.environ["TELEGRAM_BOT_TOKEN"]
    resolved_base_url = (
        base_url or os.environ.get("TELEGRAM_API_BASE_URL") or DEFAULT_TELEGRAM_API_BASE_URL
    )
    request = build_send_message_request(
        bot_token=resolved_bot_token,
        chat_id=chat_id,
        text=text,
        base_url=resolved_base_url,
    )

    with urlopen(request) as response:
        return json.load(response)

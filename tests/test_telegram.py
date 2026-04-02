from lambda_manager.telegram import build_send_message_request


def test_builds_telegram_send_message_request():
    request = build_send_message_request(
        bot_token="bot-token",
        chat_id="12345",
        text="Launched gpu_8x_a100_80gb_sxm4 in us-east-1 as instance-123",
        base_url="https://api.telegram.org",
    ).prepare()

    assert request.url == "https://api.telegram.org/botbot-token/sendMessage"
    assert request.method == "POST"
    assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert (
        request.body
        == "chat_id=12345&text=Launched+gpu_8x_a100_80gb_sxm4+in+us-east-1+as+instance-123"
    )

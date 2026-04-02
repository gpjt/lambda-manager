from unittest.mock import MagicMock, patch

import requests

from lambda_manager.http import DEFAULT_TIMEOUT_SECONDS, send_json_request


def test_send_json_request_prepares_and_sends_request():
    request = requests.Request("GET", "https://example.com/data")
    response = MagicMock()
    response.json.return_value = {"ok": True}

    session = MagicMock()
    session.send.return_value = response

    with patch("lambda_manager.http.requests.Session") as session_class:
        session_class.return_value.__enter__.return_value = session

        result = send_json_request(request)

    sent_request = session.send.call_args.args[0]
    assert sent_request.url == "https://example.com/data"
    assert session.send.call_args.kwargs["timeout"] == DEFAULT_TIMEOUT_SECONDS
    response.raise_for_status.assert_called_once_with()
    response.json.assert_called_once_with()
    assert result == {"ok": True}


def test_send_json_request_propagates_http_errors():
    request = requests.Request("GET", "https://example.com/data")
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError("boom")

    session = MagicMock()
    session.send.return_value = response

    with patch("lambda_manager.http.requests.Session") as session_class:
        session_class.return_value.__enter__.return_value = session

        try:
            send_json_request(request)
        except requests.HTTPError as exc:
            assert str(exc) == "boom"
        else:
            raise AssertionError("Expected requests.HTTPError to be raised")

    response.json.assert_not_called()

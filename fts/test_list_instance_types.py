import json
import os
import re
import subprocess
import sys
import threading
import time
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ISO_TIMESTAMP_PREFIX = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"


class LambdaStubHandler(BaseHTTPRequestHandler):
    response_body = {
        "data": {
            "gpu_1x_h100_sxm5": {
                "instance_type": {"description": "H100 SXM5"},
                "regions_with_capacity_available": [
                    {"name": "us-west-1", "description": "US West"}
                ],
            },
            "gpu_1x_a10": {
                "instance_type": {"description": "A10"},
                "regions_with_capacity_available": [],
            },
            "gpu_2x_a6000": {
                "instance_type": {"description": "2x A6000"},
                "regions_with_capacity_available": [
                    {"name": "us-east-1", "description": "US East"}
                ],
            },
        }
    }

    def do_GET(self):
        if self.path != "/instance-types":
            self.send_error(404)
            return

        auth_header = self.headers.get("Authorization")
        if auth_header != "Basic dGVzdC1hcGkta2V5Og==":
            self.send_error(401)
            return

        body = json.dumps(self.response_body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


class LaunchAndNotifyStubHandler(BaseHTTPRequestHandler):
    instance_type_requests = 0
    launch_requests = []
    telegram_requests = []

    def do_GET(self):
        if self.path == "/lambda/instance-types":
            self.__class__.instance_type_requests += 1
            if self.__class__.instance_type_requests == 1:
                response_body = {
                    "data": {
                        "gpu_8x_a100_80gb_sxm4": {
                            "instance_type": {"name": "gpu_8x_a100_80gb_sxm4"},
                            "regions_with_capacity_available": [],
                        }
                    }
                }
            else:
                response_body = {
                    "data": {
                        "gpu_8x_a100_80gb_sxm4": {
                            "instance_type": {"name": "gpu_8x_a100_80gb_sxm4"},
                            "regions_with_capacity_available": [
                                {"name": "us-east-1", "description": "Virginia, USA"}
                            ],
                        }
                    }
                }
            body = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")

        if self.path == "/lambda/instance-operations/launch":
            self.__class__.launch_requests.append(json.loads(body))
            response_body = {"data": {"instance_ids": ["instance-123"]}}
            encoded = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        if self.path.startswith("/telegram/botbot-token/sendMessage"):
            self.__class__.telegram_requests.append(parse_qs(body))
            response_body = {"ok": True, "result": {"message_id": 1}}
            encoded = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        self.send_error(404)

    def log_message(self, format, *args):
        return


class LaunchWithTelegramFailureStubHandler(BaseHTTPRequestHandler):
    launch_requests = []
    telegram_requests = []

    def do_GET(self):
        if self.path == "/lambda/instance-types":
            response_body = {
                "data": {
                    "gpu_8x_a100_80gb_sxm4": {
                        "instance_type": {"name": "gpu_8x_a100_80gb_sxm4"},
                        "regions_with_capacity_available": [
                            {"name": "us-east-1", "description": "Virginia, USA"}
                        ],
                    }
                }
            }
            body = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")

        if self.path == "/lambda/instance-operations/launch":
            self.__class__.launch_requests.append(json.loads(body))
            response_body = {"data": {"instance_ids": ["instance-456"]}}
            encoded = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        if self.path.startswith("/telegram/botbot-token/sendMessage"):
            self.__class__.telegram_requests.append(parse_qs(body))
            response_body = {"ok": False, "description": "telegram unavailable"}
            encoded = json.dumps(response_body).encode("utf-8")
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        self.send_error(404)

    def log_message(self, format, *args):
        return


class PollFailureThenSuccessStubHandler(BaseHTTPRequestHandler):
    instance_type_requests = 0

    def do_GET(self):
        if self.path == "/lambda/instance-types":
            self.__class__.instance_type_requests += 1
            if self.__class__.instance_type_requests <= 2:
                response_body = {"error": "temporary failure"}
                body = json.dumps(response_body).encode("utf-8")
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            response_body = {
                "data": {
                    "gpu_8x_a100_80gb_sxm4": {
                        "instance_type": {"name": "gpu_8x_a100_80gb_sxm4"},
                        "regions_with_capacity_available": [
                            {"name": "us-east-1", "description": "Virginia, USA"}
                        ],
                    }
                }
            }
            body = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")

        if self.path == "/lambda/instance-operations/launch":
            response_body = {"data": {"instance_ids": ["instance-789"]}}
            encoded = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        if self.path.startswith("/telegram/botbot-token/sendMessage"):
            response_body = {"ok": True, "result": {"message_id": 1}}
            encoded = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        self.send_error(404)

    def log_message(self, format, *args):
        return


class TelegramFailureThresholdStubHandler(BaseHTTPRequestHandler):
    telegram_requests = 0

    def do_GET(self):
        if self.path == "/lambda/instance-types":
            response_body = {
                "data": {
                    "gpu_8x_a100_80gb_sxm4": {
                        "instance_type": {"name": "gpu_8x_a100_80gb_sxm4"},
                        "regions_with_capacity_available": [
                            {"name": "us-east-1", "description": "Virginia, USA"}
                        ],
                    }
                }
            }
            body = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

    def do_POST(self):
        if self.path == "/lambda/instance-operations/launch":
            response_body = {"data": {"instance_ids": ["instance-999"]}}
            encoded = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        if self.path.startswith("/telegram/botbot-token/sendMessage"):
            self.__class__.telegram_requests += 1
            response_body = {"ok": False, "description": "telegram unavailable"}
            encoded = json.dumps(response_body).encode("utf-8")
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        self.send_error(404)

    def log_message(self, format, *args):
        return


class RegionFallbackStubHandler(BaseHTTPRequestHandler):
    launch_requests = []

    def do_GET(self):
        if self.path == "/lambda/instance-types":
            response_body = {
                "data": {
                    "gpu_8x_a100_80gb_sxm4": {
                        "instance_type": {"name": "gpu_8x_a100_80gb_sxm4"},
                        "regions_with_capacity_available": [
                            {"name": "us-east-1", "description": "Virginia, USA"},
                            {"name": "us-west-1", "description": "California, USA"},
                        ],
                    }
                }
            }
            body = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")

        if self.path == "/lambda/instance-operations/launch":
            payload = json.loads(body)
            self.__class__.launch_requests.append(payload)
            if payload["region_name"] == "us-east-1":
                response_body = {"error": "region launch failed"}
                encoded = json.dumps(response_body).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
                return

            response_body = {"data": {"instance_ids": ["instance-fallback"]}}
            encoded = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        if self.path.startswith("/telegram/botbot-token/sendMessage"):
            response_body = {"ok": True, "result": {"message_id": 1}}
            encoded = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        self.send_error(404)

    def log_message(self, format, *args):
        return


def run_stub_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), LambdaStubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def run_launch_and_notify_stub_server():
    LaunchAndNotifyStubHandler.instance_type_requests = 0
    LaunchAndNotifyStubHandler.launch_requests = []
    LaunchAndNotifyStubHandler.telegram_requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), LaunchAndNotifyStubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def run_launch_with_telegram_failure_stub_server():
    LaunchWithTelegramFailureStubHandler.launch_requests = []
    LaunchWithTelegramFailureStubHandler.telegram_requests = []
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), LaunchWithTelegramFailureStubHandler
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def run_poll_failure_then_success_stub_server():
    PollFailureThenSuccessStubHandler.instance_type_requests = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), PollFailureThenSuccessStubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def run_telegram_failure_threshold_stub_server():
    TelegramFailureThresholdStubHandler.telegram_requests = 0
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), TelegramFailureThresholdStubHandler
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def run_region_fallback_stub_server():
    RegionFallbackStubHandler.launch_requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), RegionFallbackStubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_lists_only_instance_types_with_capacity_available():
    server, thread = run_stub_server()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        env["LAMBDA_API_KEY"] = "test-api-key"
        env["LAMBDA_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}"

        result = subprocess.run(
            [sys.executable, "-m", "lambda_manager", "list-instance-types"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert result.returncode == 0
    assert result.stdout == "gpu_1x_h100_sxm5\ngpu_2x_a6000\n"
    assert result.stderr == ""


def test_list_instance_types_reads_configuration_from_dotenv_file():
    server, thread = run_stub_server()
    try:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / ".env").write_text(
                "\n".join(
                    [
                        "LAMBDA_API_KEY=test-api-key",
                        f"LAMBDA_API_BASE_URL=http://127.0.0.1:{server.server_port}",
                    ]
                )
                + "\n"
            )

            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            env.pop("LAMBDA_API_KEY", None)
            env.pop("LAMBDA_API_BASE_URL", None)

            result = subprocess.run(
                [sys.executable, "-m", "lambda_manager", "list-instance-types"],
                cwd=temp_path,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert result.returncode == 0
    assert result.stdout == "gpu_1x_h100_sxm5\ngpu_2x_a6000\n"
    assert result.stderr == ""


def test_poll_output_shows_regions_for_all_available_instance_types():
    server, thread = run_stub_server()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        env["LAMBDA_API_KEY"] = "test-api-key"
        env["LAMBDA_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}"
        env["LAMBDA_SSH_KEY_NAME"] = "default-key"
        env["TELEGRAM_BOT_TOKEN"] = "bot-token"
        env["TELEGRAM_CHAT_ID"] = "12345"
        env["LAMBDA_MANAGER_POLL_INTERVAL_SECONDS"] = "0.01"
        env["LAMBDA_MANAGER_MAX_CONSECUTIVE_FAILURES"] = "1"
        env["LAMBDA_MANAGER_MAX_POLLS"] = "1"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lambda_manager",
                "launch-when-available",
                "gpu_1x_a10",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert result.returncode == 0
    stdout_lines = result.stdout.splitlines()
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Available instance types: gpu_1x_h100_sxm5 \(regions: us-west-1\), gpu_2x_a6000 \(regions: us-east-1\)",
        stdout_lines[0],
    )
    assert result.stderr == ""


def test_launches_requested_instance_when_capacity_appears_and_notifies_telegram():
    server, thread = run_launch_and_notify_stub_server()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        env["LAMBDA_API_KEY"] = "test-api-key"
        env["LAMBDA_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}/lambda"
        env["LAMBDA_SSH_KEY_NAME"] = "default-key"
        env["LAMBDA_MANAGER_POLL_INTERVAL_SECONDS"] = "0.01"
        env["TELEGRAM_BOT_TOKEN"] = "bot-token"
        env["TELEGRAM_CHAT_ID"] = "12345"
        env["TELEGRAM_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}/telegram"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lambda_manager",
                "launch-when-available",
                "gpu_8x_a100_80gb_sxm4",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert result.returncode == 0
    stdout_lines = result.stdout.splitlines()
    assert len(stdout_lines) == 4
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX + r" Available instance types: none",
        stdout_lines[0],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Available instance types: gpu_8x_a100_80gb_sxm4 \(regions: us-east-1\)",
        stdout_lines[1],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Launched gpu_8x_a100_80gb_sxm4 in us-east-1 as instance-123",
        stdout_lines[2],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX + r" Telegram notification sent",
        stdout_lines[3],
    )
    assert result.stderr == ""
    assert LaunchAndNotifyStubHandler.instance_type_requests == 2
    assert LaunchAndNotifyStubHandler.launch_requests == [
        {
            "region_name": "us-east-1",
            "instance_type_name": "gpu_8x_a100_80gb_sxm4",
            "ssh_key_names": ["default-key"],
        }
    ]
    assert LaunchAndNotifyStubHandler.telegram_requests == [
        {
            "chat_id": ["12345"],
            "text": [
                "Launched gpu_8x_a100_80gb_sxm4 in us-east-1 as instance-123"
            ],
        }
    ]


def test_reports_launch_success_before_exiting_on_telegram_failure():
    server, thread = run_launch_with_telegram_failure_stub_server()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        env["LAMBDA_API_KEY"] = "test-api-key"
        env["LAMBDA_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}/lambda"
        env["LAMBDA_SSH_KEY_NAME"] = "default-key"
        env["TELEGRAM_BOT_TOKEN"] = "bot-token"
        env["TELEGRAM_CHAT_ID"] = "12345"
        env["TELEGRAM_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}/telegram"
        env["LAMBDA_MANAGER_MAX_CONSECUTIVE_FAILURES"] = "1"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lambda_manager",
                "launch-when-available",
                "gpu_8x_a100_80gb_sxm4",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert result.returncode == 1
    stdout_lines = result.stdout.splitlines()
    assert len(stdout_lines) == 3
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Available instance types: gpu_8x_a100_80gb_sxm4 \(regions: us-east-1\)",
        stdout_lines[0],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Launched gpu_8x_a100_80gb_sxm4 in us-east-1 as instance-456",
        stdout_lines[1],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Telegram API failed \(attempt 1/1\): 503 Server Error: Service Unavailable for url: http://127\.0\.0\.1:\d+/telegram/botbot-token/sendMessage",
        stdout_lines[2],
    )
    assert result.stderr == ""
    assert LaunchWithTelegramFailureStubHandler.launch_requests == [
        {
            "region_name": "us-east-1",
            "instance_type_name": "gpu_8x_a100_80gb_sxm4",
            "ssh_key_names": ["default-key"],
        }
    ]
    assert LaunchWithTelegramFailureStubHandler.telegram_requests == [
        {
            "chat_id": ["12345"],
            "text": [
                "Launched gpu_8x_a100_80gb_sxm4 in us-east-1 as instance-456"
            ],
        }
    ]


def test_retries_lambda_poll_failures_and_recovers_before_threshold():
    server, thread = run_poll_failure_then_success_stub_server()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        env["LAMBDA_API_KEY"] = "test-api-key"
        env["LAMBDA_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}/lambda"
        env["LAMBDA_SSH_KEY_NAME"] = "default-key"
        env["TELEGRAM_BOT_TOKEN"] = "bot-token"
        env["TELEGRAM_CHAT_ID"] = "12345"
        env["TELEGRAM_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}/telegram"
        env["LAMBDA_MANAGER_RETRY_DELAY_SECONDS"] = "0.01"
        env["LAMBDA_MANAGER_MAX_CONSECUTIVE_FAILURES"] = "3"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lambda_manager",
                "launch-when-available",
                "gpu_8x_a100_80gb_sxm4",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert result.returncode == 0
    stdout_lines = result.stdout.splitlines()
    assert len(stdout_lines) == 5
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Lambda API failed \(attempt 1/3\): 503 Server Error: Service Unavailable for url: http://127\.0\.0\.1:\d+/lambda/instance-types",
        stdout_lines[0],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Lambda API failed \(attempt 2/3\): 503 Server Error: Service Unavailable for url: http://127\.0\.0\.1:\d+/lambda/instance-types",
        stdout_lines[1],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Available instance types: gpu_8x_a100_80gb_sxm4 \(regions: us-east-1\)",
        stdout_lines[2],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Launched gpu_8x_a100_80gb_sxm4 in us-east-1 as instance-789",
        stdout_lines[3],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX + r" Telegram notification sent",
        stdout_lines[4],
    )
    assert result.stderr == ""


def test_exits_after_ten_consecutive_telegram_failures():
    server, thread = run_telegram_failure_threshold_stub_server()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        env["LAMBDA_API_KEY"] = "test-api-key"
        env["LAMBDA_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}/lambda"
        env["LAMBDA_SSH_KEY_NAME"] = "default-key"
        env["TELEGRAM_BOT_TOKEN"] = "bot-token"
        env["TELEGRAM_CHAT_ID"] = "12345"
        env["TELEGRAM_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}/telegram"
        env["LAMBDA_MANAGER_RETRY_DELAY_SECONDS"] = "0.01"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lambda_manager",
                "launch-when-available",
                "gpu_8x_a100_80gb_sxm4",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert result.returncode == 1
    stdout_lines = result.stdout.splitlines()
    assert len(stdout_lines) == 12
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Available instance types: gpu_8x_a100_80gb_sxm4 \(regions: us-east-1\)",
        stdout_lines[0],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Launched gpu_8x_a100_80gb_sxm4 in us-east-1 as instance-999",
        stdout_lines[1],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Telegram API failed \(attempt 10/10\): 503 Server Error: Service Unavailable for url: http://127\.0\.0\.1:\d+/telegram/botbot-token/sendMessage",
        stdout_lines[11],
    )
    assert result.stderr == ""
    assert TelegramFailureThresholdStubHandler.telegram_requests == 10


def test_falls_back_to_later_available_region_if_first_launch_region_fails():
    server, thread = run_region_fallback_stub_server()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        env["LAMBDA_API_KEY"] = "test-api-key"
        env["LAMBDA_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}/lambda"
        env["LAMBDA_SSH_KEY_NAME"] = "default-key"
        env["TELEGRAM_BOT_TOKEN"] = "bot-token"
        env["TELEGRAM_CHAT_ID"] = "12345"
        env["TELEGRAM_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}/telegram"
        env["LAMBDA_MANAGER_RETRY_DELAY_SECONDS"] = "0.01"
        env["LAMBDA_MANAGER_MAX_CONSECUTIVE_FAILURES"] = "2"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lambda_manager",
                "launch-when-available",
                "gpu_8x_a100_80gb_sxm4",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert result.returncode == 0
    stdout_lines = result.stdout.splitlines()
    assert len(stdout_lines) == 4
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Available instance types: gpu_8x_a100_80gb_sxm4 \(regions: us-east-1, us-west-1\)",
        stdout_lines[0],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Lambda launch in us-east-1 failed \(attempt 1/2\): 400 Client Error: Bad Request for url: http://127\.0\.0\.1:\d+/lambda/instance-operations/launch",
        stdout_lines[1],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Launched gpu_8x_a100_80gb_sxm4 in us-west-1 as instance-fallback",
        stdout_lines[2],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX + r" Telegram notification sent",
        stdout_lines[3],
    )
    assert result.stderr == ""
    assert RegionFallbackStubHandler.launch_requests == [
        {
            "region_name": "us-east-1",
            "instance_type_name": "gpu_8x_a100_80gb_sxm4",
            "ssh_key_names": ["default-key"],
        },
        {
            "region_name": "us-west-1",
            "instance_type_name": "gpu_8x_a100_80gb_sxm4",
            "ssh_key_names": ["default-key"],
        },
    ]

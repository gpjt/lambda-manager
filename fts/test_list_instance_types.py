import json
import os
import re
import subprocess
import sys
import threading
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
    assert len(stdout_lines) == 3
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX + r" Available instance types: none",
        stdout_lines[0],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Available instance types: gpu_8x_a100_80gb_sxm4",
        stdout_lines[1],
    )
    assert re.fullmatch(
        ISO_TIMESTAMP_PREFIX
        + r" Launched gpu_8x_a100_80gb_sxm4 in us-east-1 as instance-123",
        stdout_lines[2],
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

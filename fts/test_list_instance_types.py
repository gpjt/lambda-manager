import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


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


def run_stub_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), LambdaStubHandler)
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

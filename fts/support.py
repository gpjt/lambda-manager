import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ISO_TIMESTAMP_PREFIX = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"


class LambdaInventoryStubHandler(BaseHTTPRequestHandler):
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


def run_handler_server(handler_class):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread

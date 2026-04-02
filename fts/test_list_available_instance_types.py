import os
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from pathlib import Path

from fts.support import ISO_TIMESTAMP_PREFIX, LambdaInventoryStubHandler, REPO_ROOT, run_handler_server


def test_lists_only_instance_types_with_capacity_available():
    server, thread = run_handler_server(LambdaInventoryStubHandler)
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
    server, thread = run_handler_server(LambdaInventoryStubHandler)
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
    server, thread = run_handler_server(LambdaInventoryStubHandler)
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

import os
import subprocess
import sys

from fts.support import LambdaInventoryStubHandler, REPO_ROOT, run_handler_server


def test_lists_instance_type_descriptions_and_names_sorted_by_description():
    server, thread = run_handler_server(LambdaInventoryStubHandler)
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        env["LAMBDA_API_KEY"] = "test-api-key"
        env["LAMBDA_API_BASE_URL"] = f"http://127.0.0.1:{server.server_port}"

        result = subprocess.run(
            [sys.executable, "-m", "lambda_manager", "list-instance-type-descriptions"],
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
    assert result.stdout == (
        "description  name\n"
        "2x A6000     gpu_2x_a6000\n"
        "A10          gpu_1x_a10\n"
        "H100 SXM5    gpu_1x_h100_sxm5\n"
    )
    assert result.stderr == ""

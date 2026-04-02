# Repository Guidelines

## Project Structure & Module Organization
This repository is a Python CLI for Lambda Cloud instance discovery and launch automation. Production code lives in `src/lambda_manager/`. Keep parser/dispatch in `cli.py`, command workflows in `src/lambda_manager/commands/`, API clients in `lambda_api.py` and `telegram.py`, and shared formatting/retry helpers in `formatting.py` and `retry.py`. Functional tests live in `fts/` and are split by command area; shared FT server helpers belong in `fts/support.py`. Unit tests live in `tests/` and should stay split by responsibility, for example `test_lambda_api.py` or `test_cli_formatting.py`.

## Build, Test, and Development Commands
Development is test-first. Start each user story by turning it into a functional test in `fts/`, then drive the implementation with focused unit tests and the minimum code needed to pass.

Examples:

```bash
uv sync                                            # install project and dev dependencies
uv run pytest tests fts                           # run the full suite
uv run pytest fts/test_launch_when_available.py   # run launch workflow FTs
uv run python -m lambda_manager list-instance-types
uv run python -m lambda_manager list-instance-type-descriptions
uv run python -m lambda_manager launch-when-available gpu_8x_a100_80gb_sxm4
```

If you add a command, update both `README.md` and this file in the same change.

## Coding Style & Naming Conventions
Target Python 3 with 4-space indentation and standard PEP 8 naming: `snake_case` for functions and modules, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Keep modules small and intention-revealing. Do not let `cli.py` or any single test file become a grab bag again; split by command area or responsibility when a file starts carrying unrelated behavior. Prefer explicit imports, type hints on public interfaces, and simple command-oriented code that is easy to exercise from tests.

## Testing Guidelines
Use `pytest` throughout. Functional tests in `fts/` should describe user-visible behavior from a minimal story, while unit tests in `tests/` should pin down each implementation step before code is written. Follow strict red-green-refactor: write a failing test, make it pass with the simplest code, then refactor safely. Name files after the command or module they cover, for example `fts/test_launch_when_available.py` or `tests/test_telegram.py`. Reuse `fts/support.py` for shared subprocess/server plumbing instead of copying handlers between files.

## Commit & Pull Request Guidelines
Use short imperative commit subjects such as `Add instance type description lookup command`. Keep commits small and aligned to a single red-green-refactor step when practical. Pull requests should summarize the user story, list the tests added or updated, and include the exact commands used to verify the change.

## Preferences
- Do not add Co-Authored-By lines to commit messages.
- Prefer lambdas (with default-argument capture when needed) over functools.partial.
- Do not add friendly error handling to hide stack traces; the project is under active development and raw tracebacks are more useful for debugging. Only wrap errors when there is a specific retry/recovery strategy.

## Configuration & Security
Do not commit secrets, `.env` files, virtual environments, coverage artifacts, or local databases; those patterns are already ignored. Runtime configuration is normally loaded from a local `.env` file with keys such as `LAMBDA_API_KEY`, `LAMBDA_SSH_KEY_NAME`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID`. Treat `LAMBDA_MANAGER_TEST_MAX_POLLS` as a test-only hook; do not rely on it for user-facing behavior. When adding integrations, document required settings and provide safe defaults for local test runs.

# Repository Guidelines

## Project Structure & Module Organization
This project will grow into a tool for launching and managing Lambda Labs instances. Keep production code in `src/` and end-to-end functional tests in `fts/`. Put lower-level unit tests in `tests/`, mirroring the code layout in `src/`. Store repository configuration such as `pyproject.toml` at the root, and keep reusable test data in `fts/fixtures/` or `tests/fixtures/` as appropriate.

## Build, Test, and Development Commands
Development is test-first. Start each user story by turning it into a functional test in `fts/`, then drive the implementation with focused unit tests and the minimum code needed to pass.

Examples:

```bash
uv sync                       # install project and dev dependencies
uv run pytest fts            # run functional tests
uv run pytest tests          # run unit tests
uv run pytest                # run the full suite
```

Add any new automation in the same change that introduces it, and keep commands documented here.

## Coding Style & Naming Conventions
Target Python 3 with 4-space indentation and standard PEP 8 naming: `snake_case` for functions and modules, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Keep modules small and intention-revealing. Prefer explicit imports, type hints on public interfaces, and simple command-oriented code that is easy to exercise from tests.

## Testing Guidelines
Use `pytest` throughout. Functional tests in `fts/` should describe user-visible behavior from a minimal story, while unit tests in `tests/` should pin down each implementation step before code is written. Follow strict red-green-refactor: write a failing test, make it pass with the simplest code, then refactor safely. Name files `test_<behavior>.py` and keep fixtures close to the tests that use them.

## Commit & Pull Request Guidelines
The current history is still minimal, so use short imperative commit subjects such as `Add first instance launch functional test`. Keep commits small and aligned to a single red-green-refactor step when practical. Pull requests should summarize the user story, list the tests added or updated, and include the exact commands used to verify the change.

## Configuration & Security
Do not commit secrets, `.env` files, virtual environments, coverage artifacts, or local databases; those patterns are already ignored. Lambda Labs credentials should be injected through environment variables or a documented local-only config file. When adding integrations, document required settings and provide safe defaults for local test runs.

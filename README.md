# lambda-manager

`lambda-manager` is a small CLI for watching Lambda Cloud instance availability and launching an instance when capacity appears.

Current features:

- list instance types that are launchable right now
- poll for a specific instance type
- launch it automatically when capacity appears
- send a Telegram notification after launch

## Requirements

- Python 3.12+
- `uv`
- a Lambda Cloud API key
- a Lambda Cloud SSH key name already registered with your account
- a Telegram bot token and chat ID

## Configuration

The CLI reads a `.env` file from the current working directory on startup.

Example:

```env
LAMBDA_API_KEY=...
LAMBDA_SSH_KEY_NAME=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
LAMBDA_MANAGER_POLL_INTERVAL_SECONDS=60
```

`LAMBDA_MANAGER_POLL_INTERVAL_SECONDS` is optional and defaults to `60`.

## Telegram Setup

To use notifications, you need a bot token and a chat ID.

- Create a Telegram bot with `@BotFather` and keep the bot token it gives you.
- Start a chat with your bot. Because this project does not listen for inbound messages, that will usually just send `/start` and nothing else will happen.
- Forward that `/start` message to `@GetTheirIDBot`.
- `@GetTheirIDBot` will tell you the chat ID to use as `TELEGRAM_CHAT_ID`.

## Running the CLI

From the repository root:

```bash
uv run python -m lambda_manager list-instance-types
uv run python -m lambda_manager launch-when-available gpu_8x_a100_80gb_sxm4
```

The polling command prints an ISO timestamp on each line, reports which instance types are currently launchable, and sends a Telegram message when it successfully launches an instance.

## Development

Install dependencies and run the test suite with:

```bash
uv sync
uv run pytest
```

Tests follow the repository TDD approach:

- functional tests live in `fts/`
- unit tests live in `tests/`
- production code lives in `src/`

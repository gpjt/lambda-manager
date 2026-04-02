# lambda-manager

`lambda-manager` is a Python CLI for working with Lambda Cloud instance types and automating instance launches.

It currently does three things:

1. Show which instance types are launchable right now.
2. Show the mapping between Lambda’s human-readable instance descriptions and the API instance type names.
3. Poll for a specific instance type, launch it as soon as capacity appears, and send a Telegram notification.

## Requirements

- Python 3.12+
- `uv`
- a Lambda Cloud API key
- a Lambda Cloud SSH key name already registered with your account
- a Telegram bot token and chat ID

## Setup

Install dependencies from the repository root:

```bash
uv sync
```

## Configuration

`lambda-manager` reads a `.env` file from the current working directory on startup.

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

## Commands

From the repository root:

```bash
uv run python -m lambda_manager list-instance-types
uv run python -m lambda_manager list-instance-type-descriptions
uv run python -m lambda_manager launch-when-available gpu_8x_a100_80gb_sxm4
```

### `list-instance-types`

Prints the Lambda API instance type names that currently have launch capacity.

Example output:

```text
gpu_1x_h100_sxm5
gpu_2x_a6000
```

### `list-instance-type-descriptions`

Prints a two-column table with the website-style description and the Lambda API instance type name, sorted by description.

Example output:

```text
description  name
2x A6000     gpu_2x_a6000
A10          gpu_1x_a10
H100 SXM5    gpu_1x_h100_sxm5
```

Use this when you know the description from the website but need the exact CLI/API name.

### `launch-when-available <instance-type>`

Polls Lambda Cloud until the requested instance type is available, tries the available regions in order, launches the instance, and sends a Telegram notification.

The command:

- prints ISO-timestamped status lines
- shows all currently available instance types and their regions on each poll
- retries transient Lambda and Telegram failures
- skips regions that fail with non-retriable launch client errors

Example:

```bash
uv run python -m lambda_manager launch-when-available gpu_8x_a100_80gb_sxm4
```

## Development

Run the test suite with:

```bash
uv run pytest
```

The project follows a TDD workflow:

- functional tests live in `fts/`
- unit tests live in `tests/`
- production code lives in `src/`

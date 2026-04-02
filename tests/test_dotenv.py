import os
from pathlib import Path

from lambda_manager.dotenv import load_dotenv


def test_load_dotenv_sets_variables_from_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("LAMBDA_API_KEY=test-key\nTELEGRAM_CHAT_ID=12345\n")
    monkeypatch.delenv("LAMBDA_API_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    load_dotenv(env_file)

    assert os.environ["LAMBDA_API_KEY"] == "test-key"
    assert os.environ["TELEGRAM_CHAT_ID"] == "12345"


def test_load_dotenv_does_not_override_existing_environment(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("LAMBDA_API_KEY=file-key\n")
    monkeypatch.setenv("LAMBDA_API_KEY", "existing-key")

    load_dotenv(env_file)

    assert os.environ["LAMBDA_API_KEY"] == "existing-key"

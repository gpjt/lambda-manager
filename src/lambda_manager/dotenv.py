from pathlib import Path

from dotenv import load_dotenv as _load_dotenv


def load_dotenv(path: str | Path = ".env") -> None:
    _load_dotenv(dotenv_path=Path(path), override=False)

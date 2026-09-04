from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def load_dotenv_if_present(path: Optional[Path] = None) -> None:
    """Load KEY=VALUE pairs from .env without overwriting existing env vars.

    Values are never logged. Missing files are ignored.
    """
    candidates = [path] if path is not None else [Path(".env")]
    for envfile in candidates:
        if envfile is None or not envfile.exists():
            continue
        with envfile.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        break


def twitter_credentials_from_env() -> Optional[tuple[str, str, str]]:
    username = os.environ.get("TWITTER_USERNAME", "").strip()
    email = os.environ.get("TWITTER_EMAIL", "").strip()
    password = os.environ.get("TWITTER_PASSWORD", "").strip()
    if username and email and password:
        return username, email, password
    return None


def resolve_cookies_path(configured: Path) -> Path:
    override = os.environ.get("X_COOKIES_PATH", "").strip()
    if override:
        return Path(override)
    return configured

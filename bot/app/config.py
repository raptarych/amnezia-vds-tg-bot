"""Bot configuration loaded from a user-owned YAML secrets file.

The config file lives on the host and holds all access credentials and
authorisation settings. If the file does not exist at startup it is created
with placeholder values so that an operator can fill them in.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

#: Default location of the secrets file on the host.
DEFAULT_CONFIG_PATH = "/etc/amnezia-vds/bot.yml"

TEMPLATE = {
    "telegram_bot_token": "YOUR_BOT_TOKEN_HERE",
    "http_api_url": "http://127.0.0.1:8123",
    "http_api_secret": "YOUR_API_SECRET_HERE",
    "allowed_usernames": [
        "username1",
        "username2",
    ],
}


class BotConfig:
    """Encapsulates the parsed settings from the YAML secrets file."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    @property
    def bot_token(self) -> str:
        return str(self.data.get("telegram_bot_token", ""))

    @property
    def api_url(self) -> str:
        return str(self.data.get("http_api_url", "")).rstrip("/")

    @property
    def api_secret(self) -> str:
        return str(self.data.get("http_api_secret", ""))

    @property
    def allowed_usernames(self) -> set[str]:
        raw = self.data.get("allowed_usernames", [])
        if isinstance(raw, str):
            raw = [raw]
        return {str(item).lstrip("@") for item in raw if item}

    def is_user_allowed(self, username: str | None) -> bool:
        """Return ``True`` if a Telegram username is authorised to use the bot."""
        if not username:
            return False
        return username.lstrip("@") in self.allowed_usernames


def _merge(overrides: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override values into the template defaults."""
    result = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(value, result[key])
        else:
            result[key] = value
    return result


def load_config(path: str | None = None, *, create_if_missing: bool = True) -> BotConfig:
    """Load the bot configuration from the YAML secrets file.

    Args:
        path: Optional override for the config file location. Falls back to
            the ``BOT_CONFIG_PATH`` environment variable and then to the
            default host path.
        create_if_missing: Whether to create the file with placeholders when
            it does not exist.

    Returns:
        A :class:`BotConfig` instance.

    Raises:
        FileNotFoundError: If the file is missing and creation is disabled.
    """
    config_path = Path(
        os.environ.get("BOT_CONFIG_PATH") or path or DEFAULT_CONFIG_PATH
    )
    if not config_path.exists():
        if not create_if_missing:
            raise FileNotFoundError(f"Config file not found: {config_path}")
        config_path.write_text(
            yaml.safe_dump(TEMPLATE, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        print(f"Created config stub at {config_path}. Fill it in and restart.")

    raw: dict[str, Any] = yaml.safe_load(
        config_path.read_text(encoding="utf-8")
    ) or {}
    data = _merge(raw, TEMPLATE)
    return BotConfig(data)

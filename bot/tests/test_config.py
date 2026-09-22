"""Tests for the bot configuration parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import BotConfig, load_config


def test_load_config_creates_stub(tmp_path: Path) -> None:
    path = tmp_path / "bot.yml"
    cfg = load_config(str(path))
    assert path.exists()
    assert cfg.bot_token == "YOUR_BOT_TOKEN_HERE"
    assert cfg.api_secret == "YOUR_API_SECRET_HERE"
    assert cfg.api_url == "http://127.0.0.1:8123"


def test_load_config_requires_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "bot.yml"
    with pytest.raises(FileNotFoundError):
        load_config(str(path), create_if_missing=False)


def test_load_config_parses_values(tmp_path: Path) -> None:
    path = tmp_path / "bot.yml"
    path.write_text(
        "\n".join(
            [
                "telegram_bot_token: real-token",
                "http_api_url: http://example.com:9000",
                "http_api_secret: s3cret",
                "allowed_usernames:",
                "  - '@alice'",
                "  - bob",
            ]
        ),
        encoding="utf-8",
    )
    cfg = load_config(str(path))
    assert cfg.bot_token == "real-token"
    assert cfg.api_secret == "s3cret"
    assert cfg.allowed_usernames == {"alice", "bob"}
    assert cfg.is_user_allowed("@alice") is True
    assert cfg.is_user_allowed("bob") is True
    assert cfg.is_user_allowed("carol") is False
    assert cfg.is_user_allowed(None) is False

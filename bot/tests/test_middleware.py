"""Tests for the access-control middleware."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from aiogram.types import CallbackQuery, Chat, Message, User

from app.config import BotConfig
from app.middleware import AccessMiddleware


def _user(username: str | None = "alice", uid: int = 1) -> User:
    return User(id=uid, is_bot=False, first_name="A", username=username)


def _message(user: User, text: str = "/help") -> Message:
    return Message(
        message_id=1,
        date=1,
        chat=Chat(id=1, type="private"),
        from_user=user,
        text=text,
    )


def _config(username: str = "alice") -> BotConfig:
    return BotConfig(
        {
            "telegram_bot_token": "x",
            "http_api_url": "http://x",
            "http_api_secret": "s",
            "allowed_usernames": [username],
        }
    )


async def _noop_handler(event, data: dict[str, Any]) -> str:
    return "handled"


@pytest.mark.asyncio
async def test_allowed_message_passes_through() -> None:
    mw = AccessMiddleware(_config())
    result = await mw(_noop_handler, _message(_user()), {})
    assert result == "handled"


@pytest.mark.asyncio
async def test_disallowed_message_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Message, "answer", AsyncMock())
    mw = AccessMiddleware(_config("bob"))
    result = await mw(_noop_handler, _message(_user("alice")), {})
    assert result is None


@pytest.mark.asyncio
async def test_allowed_callback_passes_through() -> None:
    mw = AccessMiddleware(_config())
    cbq = CallbackQuery(
        id="1",
        from_user=_user(),
        chat_instance="c",
        data="confirm_restart",
        message=_message(_user()),
    )
    result = await mw(_noop_handler, cbq, {})
    assert result == "handled"


@pytest.mark.asyncio
async def test_disallowed_callback_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CallbackQuery, "answer", AsyncMock())
    mw = AccessMiddleware(_config("bob"))
    cbq = CallbackQuery(
        id="1",
        from_user=_user("alice"),
        chat_instance="c",
        data="confirm_restart",
        message=_message(_user("alice")),
    )
    result = await mw(_noop_handler, cbq, {})
    assert result is None

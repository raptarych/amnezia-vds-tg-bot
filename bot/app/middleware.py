"""Access-control middleware for the bot.

Every incoming update is checked against the allow-list of Telegram
usernames. Unauthorised senders get a short notice and their update is not
propagated to any command handler.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Update

from .config import BotConfig


class AccessMiddleware(BaseMiddleware):
    """Reject updates from users not present in the config allow-list."""

    def __init__(self, config: BotConfig) -> None:
        self._config = config

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        sender = None
        reply_to = None

        if event.message is not None:
            sender = event.message.from_user
            reply_to = event.message
        elif event.callback_query is not None:
            sender = event.callback_query.from_user
            reply_to = event.callback_query.message

        if sender is None:
            return None

        username = sender.username if sender is not None else None

        if not self._config.is_user_allowed(username):
            if reply_to is not None:
                await reply_to.answer("У вас нет доступа к этому боту.")
            return None

        return await handler(event, data)

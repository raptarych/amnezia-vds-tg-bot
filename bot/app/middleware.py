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
from .logging_setup import access_logger


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
        update_type = "?" 

        if event.message is not None:
            sender = event.message.from_user
            reply_to = event.message
            update_type = "message"
        elif event.callback_query is not None:
            sender = event.callback_query.from_user
            reply_to = event.callback_query.message
            update_type = "callback"

        if sender is None:
            access_logger.debug("Ignoring update without a sender (type=%s)", update_type)
            return None

        username = sender.username if sender is not None else None
        user_id = sender.id

        if not self._config.is_user_allowed(username):
            access_logger.warning(
                "Denied access: user_id=%s username=%r type=%s",
                user_id,
                username,
                update_type,
            )
            if reply_to is not None:
                await reply_to.answer("У вас нет доступа к этому боту.")
            return None

        access_logger.info(
            "Handling %s from user_id=%s username=%r", update_type, user_id, username
        )
        return await handler(event, data)

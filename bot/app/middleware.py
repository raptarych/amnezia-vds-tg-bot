"""Access-control middleware for the bot.

Every incoming update is checked against the allow-list of Telegram
usernames. Unauthorised senders get a short notice and their update is not
propagated to any command handler.

Note: this middleware is registered on the ``dp.message`` and
``dp.callback_query`` observers, so it receives the observed event directly
(a :class:`Message` or :class:`CallbackQuery`), not a whole :class:`Update`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from .config import BotConfig
from .logging_setup import access_logger


class AccessMiddleware(BaseMiddleware):
    """Reject updates from users not present in the config allow-list."""

    def __init__(self, config: BotConfig) -> None:
        self._config = config

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            sender = event.from_user
            reply_to = event
            update_type = "message"
        elif isinstance(event, CallbackQuery):
            sender = event.from_user
            reply_to = event.message
            update_type = "callback"
        else:
            access_logger.debug("Ignoring unsupported event type: %r", type(event))
            return None

        if sender is None:
            access_logger.debug("Ignoring %s without a sender", update_type)
            return None

        username = sender.username
        user_id = sender.id

        if not self._config.is_user_allowed(username):
            access_logger.warning(
                "Denied access: user_id=%s username=%r type=%s",
                user_id,
                username,
                update_type,
            )
            if reply_to is not None:
                if update_type == "callback":
                    await event.answer("У вас нет доступа к этому боту.")
                else:
                    await reply_to.answer("У вас нет доступа к этому боту.")
            return None

        access_logger.info(
            "Handling %s from user_id=%s username=%r", update_type, user_id, username
        )
        return await handler(event, data)

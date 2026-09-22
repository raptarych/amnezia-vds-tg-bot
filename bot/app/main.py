"""Bot entrypoint using Telegram long-polling.

Loads the YAML secrets file (creating a placeholder one if missing), wires up
the generated API client and starts polling for updates.
"""

from __future__ import annotations

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .api import AmneziaClient
from .config import load_config
from .handlers.commands import router as commands_router
from .logging_setup import bot_logger, configure_logging, normalize_level
from .middleware import AccessMiddleware


async def main() -> None:
    """Run the bot until interrupted."""
    config = load_config()
    configure_logging(
        level=normalize_level(config.log_level), log_file=config.log_file or None
    )

    if not config.bot_token or config.bot_token.startswith("YOUR_"):
        bot_logger.error(
            "Set a valid telegram_bot_token in the config file and restart."
        )
        sys.exit(1)

    api = AmneziaClient.from_config(config)

    bot = Bot(token=config.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.outer_middleware(AccessMiddleware(config))
    dp.callback_query.outer_middleware(AccessMiddleware(config))

    dp.include_router(commands_router)

    dp["amnezia"] = api

    bot_logger.info("Bot starting; polling for updates from the API at %s", config.api_url)
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        bot_logger.info("Bot stopped.")

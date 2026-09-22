"""Bot entrypoint using Telegram long-polling.

Loads the YAML secrets file (creating a placeholder one if missing), wires up
the generated API client and starts polling for updates.
"""

from __future__ import annotations

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from . import handlers
from .api import AmneziaClient
from .config import load_config
from .middleware import AccessMiddleware


async def main() -> None:
    """Run the bot until interrupted."""
    config = load_config()

    if not config.bot_token or config.bot_token.startswith("YOUR_"):
        print("ERROR: Set a valid telegram_bot_token in the config file.")
        sys.exit(1)

    api = AmneziaClient.from_config(config)

    bot = Bot(token=config.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.outer_middleware(AccessMiddleware(config))
    dp.callback_query.outer_middleware(AccessMiddleware(config))

    dp.include_router(handlers.commands.router)

    dp["amnezia"] = api

    print("Bot started, polling for updates...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")

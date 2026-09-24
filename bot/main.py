import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import load_config
from bot.database import Database
from bot.handlers import commands
from bot.middlewares import MemberTrackingMiddleware


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    config = load_config()

    db = Database(config.database_path)
    await db.init()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp["db"] = db
    dp["config"] = config

    dp.message.outer_middleware(MemberTrackingMiddleware(db))
    dp.include_router(commands.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import load_config
from bot.database import Database
from bot.handlers import chats, commands, replies
from bot.middlewares import MemberTrackingMiddleware
from bot.scheduler import run_scheduler


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
    dp.include_router(chats.router)
    dp.include_router(commands.router)
    dp.include_router(replies.router)

    scheduler_task = asyncio.create_task(
        run_scheduler(bot, db, config.questions_file, config.question_interval_hours)
    )

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        scheduler_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())

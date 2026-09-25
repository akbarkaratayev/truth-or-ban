import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from bot.asking import ask_question
from bot.database import Database
from bot.questions import load_questions

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 300


async def run_scheduler(
    bot: Bot, db: Database, questions_file: str, interval_hours: float
) -> None:
    """Background loop: asks a question in each active chat roughly every
    `interval_hours`, checking periodically rather than sleeping for the
    full interval so a freshly active chat doesn't have to wait a full
    cycle for its first check.
    """
    interval = timedelta(hours=interval_hours)
    while True:
        try:
            await _tick(bot, db, questions_file, interval)
        except Exception:
            logger.exception("Scheduled question tick failed")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def _tick(bot: Bot, db: Database, questions_file: str, interval: timedelta) -> None:
    questions = load_questions(questions_file)
    now = datetime.now(timezone.utc)

    for chat_id in await db.get_active_chats():
        last_asked_at = await db.get_last_question_time(chat_id)
        if last_asked_at is not None and now - last_asked_at < interval:
            continue

        try:
            result = await ask_question(bot, db, chat_id, questions)
        except (TelegramBadRequest, TelegramForbiddenError):
            logger.warning(
                "Chat %s is no longer reachable (bot not in it, or it was "
                "deleted) - marking inactive.",
                chat_id,
            )
            await db.mark_chat_inactive(chat_id)
            continue

        if result:
            logger.info("Skipped scheduled question for chat %s: %s", chat_id, result)

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot

from bot.asking import ask_question
from bot.database import Database
from bot.questions import load_questions

logger = logging.getLogger(__name__)

MIN_CHECK_INTERVAL_SECONDS = 15
MAX_CHECK_INTERVAL_SECONDS = 300


async def run_scheduler(
    bot: Bot, db: Database, questions_file: str, interval_hours: float
) -> None:
    """Background loop: asks a question in each active chat roughly every
    `interval_hours`, checking periodically rather than sleeping for the
    full interval so a freshly active chat doesn't have to wait a full
    cycle for its first check.

    How often it checks scales with the configured interval (capped between
    15s and 5min), so a short interval used for testing is actually
    respected instead of being rounded up to a fixed 5-minute granularity.
    """
    interval = timedelta(hours=interval_hours)
    check_interval = min(
        MAX_CHECK_INTERVAL_SECONDS,
        max(MIN_CHECK_INTERVAL_SECONDS, interval.total_seconds() / 5),
    )
    while True:
        try:
            await _tick(bot, db, questions_file, interval)
        except Exception:
            logger.exception("Scheduled question tick failed")
        await asyncio.sleep(check_interval)


async def _tick(bot: Bot, db: Database, questions_file: str, interval: timedelta) -> None:
    questions = load_questions(questions_file)
    now = datetime.now(timezone.utc)

    for chat_id in await db.get_active_chats():
        last_asked_at = await db.get_last_question_time(chat_id)
        if last_asked_at is not None and now - last_asked_at < interval:
            continue

        result = await ask_question(bot, db, chat_id, questions)
        if result:
            logger.info("Skipped scheduled question for chat %s: %s", chat_id, result)

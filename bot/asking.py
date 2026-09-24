import random

from aiogram import Bot

from bot.database import Database
from bot.utils import display_name, mention_html


async def choose_target(db: Database, chat_id: int, members: list[dict]) -> dict | None:
    if not members:
        return None

    last_user_id = await db.get_last_asked_user(chat_id)
    candidates = members
    if last_user_id is not None and len(members) > 1:
        others = [m for m in members if m["user_id"] != last_user_id]
        if others:
            candidates = others

    return random.choice(candidates)


async def choose_question(
    db: Database, chat_id: int, user_id: int, questions: list[str]
) -> str | None:
    if not questions:
        return None

    already_asked = await db.get_asked_questions(chat_id, user_id)
    available = [q for q in questions if q not in already_asked]
    if not available:
        return None

    return random.choice(available)


async def ask_question(
    bot: Bot, db: Database, chat_id: int, questions: list[str]
) -> str | None:
    """Picks a member and an unused question, sends it, and logs it.

    Returns None on success, or a short reason code ("no_members" /
    "no_questions") if it couldn't ask anyone.
    """
    members = await db.get_active_members(chat_id)
    target = await choose_target(db, chat_id, members)
    if target is None:
        return "no_members"

    question = await choose_question(db, chat_id, target["user_id"], questions)
    if question is None:
        return "no_questions"

    name = display_name(
        target["user_id"], target["first_name"], target["last_name"], target["username"]
    )
    mention = mention_html(target["user_id"], name)
    sent = await bot.send_message(chat_id, f"{mention}, {question}")

    await db.log_question(
        chat_id=chat_id,
        user_id=target["user_id"],
        user_name=name,
        question=question,
        message_id=sent.message_id,
    )
    return None

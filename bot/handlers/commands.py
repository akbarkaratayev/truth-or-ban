from aiogram import Bot, Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import Message

from bot.asking import ask_question
from bot.config import Config
from bot.database import Database
from bot.history import format_history
from bot.questions import load_questions

router = Router(name="commands")

ADMIN_STATUSES = {ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR}
GROUP_TYPES = {"group", "supergroup"}

HELP_TEXT = (
    "Hi! I'm the Truth-or-... bot 👋\n\n"
    "Every so often I pick a random member of this group and ask them a "
    "personal question by mentioning them. When that person replies to my "
    "question, I save their answer so they can build up their own "
    "question-and-answer history over time.\n\n"
    "Commands:\n"
    "/myanswers — see your own saved questions and answers\n"
    "/deletemyanswers — delete all of your saved answers\n"
    "/ask — (admins only) ask a question right now\n"
    "/answers @user — (admins only) see someone else's history\n"
    "/help — show this message"
)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.reply(HELP_TEXT)


@router.message(Command("ask"))
async def cmd_ask(message: Message, bot: Bot, db: Database, config: Config) -> None:
    if message.chat.type not in GROUP_TYPES:
        await message.reply("This command only works inside a group.")
        return

    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ADMIN_STATUSES:
        await message.reply("Only group admins can use /ask.")
        return

    questions = load_questions(config.questions_file)
    result = await ask_question(bot, db, message.chat.id, questions)

    if result == "no_members":
        await message.reply(
            "I don't know any group members yet — I learn about people as "
            "they send messages, so ask someone to say something first."
        )
    elif result == "no_questions":
        await message.reply(
            "I've already asked everyone I know every question I have — "
            "add more to questions.txt."
        )


@router.message(Command("myanswers"))
async def cmd_myanswers(message: Message, bot: Bot, db: Database, bot_username: str) -> None:
    user = message.from_user
    if user is None:
        return

    entries = await db.get_user_history(user.id)
    chunks = format_history(entries) or ["You don't have any saved answers yet."]

    try:
        for chunk in chunks:
            await bot.send_message(user.id, chunk)
        if message.chat.id != user.id:
            await message.reply("I've sent your answers in a private message 📬")
    except TelegramForbiddenError:
        await message.reply(
            "I can't message you privately yet — start a chat with me first: "
            f"https://t.me/{bot_username}, then run /myanswers again."
        )

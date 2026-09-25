from aiogram import Bot, F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.asking import ask_question
from bot.config import Config
from bot.database import Database
from bot.history import format_history
from bot.questions import load_questions
from bot.utils import display_name, mention_html

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
    "/answers @user (or reply to their message) — (admins only) see someone else's history\n"
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


@router.message(Command("answers"))
async def cmd_answers(message: Message, bot: Bot, db: Database, bot_username: str) -> None:
    if message.chat.type not in GROUP_TYPES:
        await message.reply("This command only works inside a group.")
        return

    admin = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if admin.status not in ADMIN_STATUSES:
        await message.reply("Only group admins can use /answers.")
        return

    args = (message.text or "").split(maxsplit=1)
    username_arg = None
    if len(args) > 1 and args[1].strip().startswith("@"):
        username_arg = args[1].strip().lstrip("@")

    replied_user = message.reply_to_message.from_user if message.reply_to_message else None

    if username_arg:
        target = await db.find_member_by_username(message.chat.id, username_arg)
        if target is None:
            await message.reply(f"I don't know anyone named @{username_arg} in this group.")
            return
        target_id = target["user_id"]
        name = display_name(
            target["user_id"], target["first_name"], target["last_name"], target["username"]
        )
    elif replied_user is not None and not replied_user.is_bot:
        target_id = replied_user.id
        name = display_name(
            replied_user.id, replied_user.first_name, replied_user.last_name, replied_user.username
        )
    else:
        await message.reply(
            "Usage: /answers @username, or reply to one of their messages with "
            "/answers — handy for members who don't have a username."
        )
        return

    entries = await db.get_user_history(target_id)
    chunks = format_history(entries) or [f"{name} hasn't answered any questions yet."]
    chunks[0] = f"History for {mention_html(target_id, name)}:\n\n" + chunks[0]

    requester = message.from_user
    try:
        for chunk in chunks:
            await bot.send_message(requester.id, chunk)
        if message.chat.id != requester.id:
            await message.reply(f"I've sent {name}'s answers to you in a private message 📬")
    except TelegramForbiddenError:
        await message.reply(
            "I can't message you privately yet — start a chat with me first: "
            f"https://t.me/{bot_username}, then run /answers again."
        )


@router.message(Command("deletemyanswers"))
async def cmd_deletemyanswers(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Yes, delete them", callback_data=f"delanswers:yes:{user.id}"
                ),
                InlineKeyboardButton(
                    text="Not yet", callback_data=f"delanswers:no:{user.id}"
                ),
            ]
        ]
    )
    await message.reply(
        "Are you sure you want to delete all of your saved answers? "
        "This can't be undone.",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("delanswers:"))
async def on_delete_confirmation(callback: CallbackQuery, db: Database) -> None:
    _, action, owner_id = callback.data.split(":")
    if str(callback.from_user.id) != owner_id:
        await callback.answer("This confirmation isn't for you.", show_alert=True)
        return

    if action == "yes":
        deleted = await db.delete_user_history(int(owner_id))
        text = (
            f"Deleted {deleted} saved answer(s). 🗑️"
            if deleted
            else "You didn't have any saved answers."
        )
    else:
        text = "Okay, your answers are safe — nothing was deleted."

    await callback.message.edit_text(text, reply_markup=None)
    await callback.answer()

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="commands")

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

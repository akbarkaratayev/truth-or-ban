from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, ReactionTypeEmoji

from bot.database import Database
from bot.utils import mention_html

router = Router(name="replies")

GROUP_TYPES = {"group", "supergroup"}
THANKS_REACTION = "🙏"


@router.message(F.reply_to_message, F.chat.type.in_(GROUP_TYPES))
async def on_reply(message: Message, bot: Bot, db: Database) -> None:
    replied = message.reply_to_message
    if replied.from_user is None or replied.from_user.id != bot.id:
        return  # not a reply to one of the bot's own messages

    user = message.from_user
    if user is None or user.is_bot:
        return

    log_entry = await db.get_question_by_message_id(message.chat.id, replied.message_id)
    if log_entry is None:
        return  # reply to some other bot message, not a tracked question

    if user.id != log_entry["user_id"]:
        target_mention = mention_html(log_entry["user_id"], log_entry["user_name"])
        await message.reply(
            f"That question wasn't for you — it's {target_mention}'s to answer 🙂"
        )
        return

    if log_entry["date_answered"] is not None:
        return  # only the first reply from the chosen member counts

    answer_text = message.text or message.caption or "[non-text reply]"
    await db.save_answer(log_entry["id"], answer_text)

    try:
        await bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reaction=[ReactionTypeEmoji(emoji=THANKS_REACTION)],
        )
    except TelegramBadRequest:
        await message.reply("Thanks for sharing! 🙏")

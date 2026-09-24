from aiogram import Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated

from bot.database import Database

router = Router(name="chats")

GROUP_TYPES = {"group", "supergroup"}
ACTIVE_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.CREATOR,
}


@router.my_chat_member()
async def on_bot_membership_changed(update: ChatMemberUpdated, db: Database) -> None:
    if update.chat.type not in GROUP_TYPES:
        return

    if update.new_chat_member.status in ACTIVE_STATUSES:
        await db.mark_chat_active(update.chat.id)
    else:
        await db.mark_chat_inactive(update.chat.id)

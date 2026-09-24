from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from bot.database import Database

GROUP_TYPES = {"group", "supergroup"}


class MemberTrackingMiddleware(BaseMiddleware):
    """Keeps the members table in sync with who is active in each group.

    Runs as an outer middleware so it tracks senders/joins/leaves on every
    update, regardless of which (if any) handler ends up processing it.
    """

    def __init__(self, db: Database):
        self.db = db

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if event.chat.type in GROUP_TYPES:
            await self.db.mark_chat_active(event.chat.id)

            if event.new_chat_members:
                for user in event.new_chat_members:
                    if not user.is_bot:
                        await self.db.upsert_member(
                            chat_id=event.chat.id,
                            user_id=user.id,
                            username=user.username,
                            first_name=user.first_name,
                            last_name=user.last_name,
                        )

            if event.left_chat_member and not event.left_chat_member.is_bot:
                await self.db.deactivate_member(
                    chat_id=event.chat.id, user_id=event.left_chat_member.id
                )

            if event.from_user and not event.from_user.is_bot:
                await self.db.upsert_member(
                    chat_id=event.chat.id,
                    user_id=event.from_user.id,
                    username=event.from_user.username,
                    first_name=event.from_user.first_name,
                    last_name=event.from_user.last_name,
                )

        return await handler(event, data)

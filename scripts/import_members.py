"""One-off script to seed the bot's members table with a group's full
participant list, using a real Telegram user account via MTProto - the
Bot API has no way to list members who haven't posted in the group.

Setup:
    1. Get TELEGRAM_API_ID and TELEGRAM_API_HASH from https://my.telegram.org
       and add them to .env.
    2. Run: python -m scripts.import_members <chat_username_or_id>
       With no argument, it lists the groups your account is in so you can
       find the right identifier.

The first run asks you to log in with your phone number (a Telegram login
code, and your 2FA password if you have one). After that, a local session
file (member_import.session) keeps you logged in - it's equivalent to
being logged into your account, so never share or commit it.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.utils import get_peer_id

from bot.database import Database

load_dotenv()

SESSION_NAME = "member_import"


async def list_groups(client: TelegramClient) -> None:
    print("Your groups (rerun with one of these as the argument):\n")
    async for dialog in client.iter_dialogs():
        if not (dialog.is_group or dialog.is_channel):
            continue
        entity = dialog.entity
        identifier = (
            f"@{entity.username}" if getattr(entity, "username", None) else get_peer_id(entity)
        )
        print(f"  {identifier}\t{dialog.name}")


async def import_members(client: TelegramClient, db: Database, target: str) -> None:
    try:
        target_value: int | str = int(target)
    except ValueError:
        target_value = target.strip().lstrip("@")

    entity = await client.get_entity(target_value)
    chat_id = get_peer_id(entity)

    imported = 0
    skipped_bots = 0
    async for user in client.iter_participants(entity):
        if user.bot:
            skipped_bots += 1
            continue
        await db.upsert_member(
            chat_id=chat_id,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        imported += 1

    await db.mark_chat_active(chat_id)
    print(f"Imported {imported} member(s) into chat {chat_id} (skipped {skipped_bots} bot(s)).")


async def main() -> None:
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        print(
            "Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env "
            "(get them from https://my.telegram.org)."
        )
        sys.exit(1)

    database_path = os.getenv("DATABASE_PATH", "bot.db")
    db = Database(database_path)
    await db.init()

    client = TelegramClient(SESSION_NAME, int(api_id), api_hash)
    await client.start()

    if len(sys.argv) != 2:
        await list_groups(client)
        await client.disconnect()
        return

    await import_members(client, db, sys.argv[1])
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

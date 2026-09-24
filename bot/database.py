from datetime import datetime, timezone

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS members (
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, chat_id)
);
"""


class Database:
    def __init__(self, path: str):
        self._path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.executescript(SCHEMA)
            await db.commit()

    async def upsert_member(
        self,
        chat_id: int,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                INSERT INTO members (user_id, chat_id, username, first_name, last_name, is_active, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT (user_id, chat_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    is_active = 1,
                    updated_at = excluded.updated_at
                """,
                (user_id, chat_id, username, first_name, last_name, now),
            )
            await db.commit()

    async def deactivate_member(self, chat_id: int, user_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                UPDATE members SET is_active = 0, updated_at = ?
                WHERE chat_id = ? AND user_id = ?
                """,
                (now, chat_id, user_id),
            )
            await db.commit()

    async def get_active_members(self, chat_id: int) -> list[dict]:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT user_id, username, first_name, last_name
                FROM members
                WHERE chat_id = ? AND is_active = 1
                """,
                (chat_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

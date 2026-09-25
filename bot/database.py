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

CREATE TABLE IF NOT EXISTS chats (
    chat_id INTEGER PRIMARY KEY,
    is_active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_name TEXT NOT NULL,
    question TEXT NOT NULL,
    message_id INTEGER,
    date_asked TEXT NOT NULL,
    date_answered TEXT,
    answer TEXT
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

    async def log_question(
        self,
        chat_id: int,
        user_id: int,
        user_name: str,
        question: str,
        message_id: int | None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self._path) as db:
            cursor = await db.execute(
                """
                INSERT INTO questions_log (chat_id, user_id, user_name, question, message_id, date_asked)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chat_id, user_id, user_name, question, message_id, now),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_asked_questions(self, chat_id: int, user_id: int) -> set[str]:
        async with aiosqlite.connect(self._path) as db:
            cursor = await db.execute(
                "SELECT question FROM questions_log WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id),
            )
            rows = await cursor.fetchall()
            return {row[0] for row in rows}

    async def get_last_asked_user(self, chat_id: int) -> int | None:
        async with aiosqlite.connect(self._path) as db:
            cursor = await db.execute(
                "SELECT user_id FROM questions_log WHERE chat_id = ? ORDER BY id DESC LIMIT 1",
                (chat_id,),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def get_ask_counts(self, chat_id: int) -> dict[int, int]:
        async with aiosqlite.connect(self._path) as db:
            cursor = await db.execute(
                "SELECT user_id, COUNT(*) FROM questions_log WHERE chat_id = ? GROUP BY user_id",
                (chat_id,),
            )
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}

    async def get_question_by_message_id(
        self, chat_id: int, message_id: int
    ) -> dict | None:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, user_id, user_name, question, date_answered
                FROM questions_log
                WHERE chat_id = ? AND message_id = ?
                """,
                (chat_id, message_id),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def save_answer(self, log_id: int, answer: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                "UPDATE questions_log SET answer = ?, date_answered = ? WHERE id = ?",
                (answer, now, log_id),
            )
            await db.commit()

    async def get_last_question_time(self, chat_id: int) -> datetime | None:
        async with aiosqlite.connect(self._path) as db:
            cursor = await db.execute(
                "SELECT date_asked FROM questions_log WHERE chat_id = ? ORDER BY id DESC LIMIT 1",
                (chat_id,),
            )
            row = await cursor.fetchone()
            return datetime.fromisoformat(row[0]) if row else None

    async def mark_chat_active(self, chat_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                INSERT INTO chats (chat_id, is_active, updated_at)
                VALUES (?, 1, ?)
                ON CONFLICT (chat_id) DO UPDATE SET is_active = 1, updated_at = excluded.updated_at
                """,
                (chat_id, now),
            )
            await db.commit()

    async def mark_chat_inactive(self, chat_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                INSERT INTO chats (chat_id, is_active, updated_at)
                VALUES (?, 0, ?)
                ON CONFLICT (chat_id) DO UPDATE SET is_active = 0, updated_at = excluded.updated_at
                """,
                (chat_id, now),
            )
            await db.commit()

    async def get_user_history(self, user_id: int) -> list[dict]:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT chat_id, question, answer, date_asked, date_answered
                FROM questions_log
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (user_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_active_chats(self) -> list[int]:
        async with aiosqlite.connect(self._path) as db:
            cursor = await db.execute("SELECT chat_id FROM chats WHERE is_active = 1")
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

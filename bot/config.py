import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    question_interval_hours: float
    database_path: str
    questions_file: str


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN is not set. Copy .env.example to .env and fill it in."
        )
    return Config(
        bot_token=token,
        question_interval_hours=float(os.getenv("QUESTION_INTERVAL_HOURS", "6")),
        database_path=os.getenv("DATABASE_PATH", "bot.db"),
        questions_file=os.getenv("QUESTIONS_FILE", "questions.txt"),
    )

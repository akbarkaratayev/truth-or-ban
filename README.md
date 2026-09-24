# Truth or... (Telegram Group Question Bot)

A Telegram bot that periodically picks a random member of a group, asks
them a personal question, and builds up a private question-and-answer
history for each user.

> **Status:** work in progress, built in stages. Currently implemented:
> member tracking and `/help`. Scheduled questions, answer collection, and
> the history commands are coming in later stages.

## 1. Install dependencies

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Create a bot with @BotFather

1. Open [@BotFather](https://t.me/BotFather) in Telegram and run `/newbot`,
   then follow the prompts to get a bot token.
2. **Disable privacy mode** so the bot can see all messages in the group
   (not just commands and replies to it):
   - Send `/mybots` to @BotFather.
   - Choose your bot → **Bot Settings** → **Group Privacy** → **Turn off**.
   - If the bot is already in a group, remove it and re-add it after
     turning privacy off (privacy mode is applied when the bot joins).

## 3. Configure the .env file

```bash
cp .env.example .env
```

Edit `.env` and set:

- `BOT_TOKEN` — the token from @BotFather.
- `QUESTION_INTERVAL_HOURS` — how often to ask a question (default `6`).
- `DATABASE_PATH` — where the SQLite file is stored (default `bot.db`).
- `QUESTIONS_FILE` — path to the question list (default `questions.txt`).

Edit `questions.txt` to add or change the questions the bot can ask (one
per line).

## 4. Run the bot

```bash
python -m bot.main
```

The bot uses long polling, so it just needs outbound internet access —
no public URL or webhook is required. This makes it easy to run locally
first and move to a VPS later.

## 5. Add it to a group

Add the bot to your Telegram group as a member. Once privacy mode is off
(step 2), it will start tracking members as they send messages or
join/leave. Try `/help` in the group to confirm it's running.

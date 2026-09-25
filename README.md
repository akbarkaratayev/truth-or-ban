# Truth or... (Telegram Group Question Bot)

A Telegram bot that periodically picks a random member of a group, asks
them a personal question, and builds up a private question-and-answer
history for each user.

> **Status:** work in progress. Member tracking, scheduled + on-demand
> questions, answer collection, and the history commands (`/myanswers`,
> `/answers`, `/deletemyanswers`) are all implemented. Deployment docs are
> coming in a later stage.

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

## 6. (Optional) Import a group's existing member list

The Bot API has no way to list a group's full membership — the bot only
learns about people as they send messages or join *after* it's added. If
you want everyone included right away (not just people who happen to post),
`scripts/import_members.py` can seed the database using your own Telegram
account instead of the bot:

1. Get an `api_id` and `api_hash` from <https://my.telegram.org> (log in
   with your own phone number, "API development tools") and set
   `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` in `.env`.
2. Run it with no argument to list the groups your account is in:
   ```bash
   python -m scripts.import_members
   ```
3. Run it again with the group's `@username` or the id printed above:
   ```bash
   python -m scripts.import_members @mygroup
   ```

The first run asks you to log in with your phone number (a login code,
plus your 2FA password if you have one). This creates a local
`member_import.session` file so you don't have to log in again — treat
that file like a password (it's already excluded from git via
`.gitignore`); anyone with it can act as your Telegram account until you
revoke the session from Telegram's Settings → Devices.

This only needs to be run once per group (or again later if a lot of new
people join without posting) — it's a separate one-off script, not part
of the bot's normal operation.

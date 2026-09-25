# Truth or... (Telegram Group Question Bot)

A Telegram bot that periodically picks a random member of a group, asks
them a personal question, and builds up a private question-and-answer
history for each user.

> **Status:** all core features are implemented — member tracking,
> scheduled + on-demand questions, answer collection, the history
> commands (`/myanswers`, `/answers`, `/deletemyanswers`), and VPS
> deployment via `systemd`.

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

## 7. Deploy to a VPS (run it 24/7)

The bot uses long polling, so deployment just means getting the code
running continuously on a server — no public URL, domain, or webhook
setup required.

### 7.1. Get the code and dependencies onto the VPS

SSH into your VPS, then:

```bash
git clone <your-repo-url> truth-or-ban
cd truth-or-ban
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # fill in BOT_TOKEN and the rest, same as the local setup
```

### 7.2. Bring over your existing database (optional)

If you've already been running the bot locally and want to keep its
data (members, questions asked, answers), stop the local bot first,
then copy the database file over — it's a single file, no export/import
needed:

```bash
scp bot.db youruser@your-vps-ip:/home/youruser/truth-or-ban/bot.db
```

Don't run the bot locally and on the VPS at the same time against the
same `BOT_TOKEN` — two pollers racing for the same updates causes
unpredictable behavior. Once the VPS copy is confirmed working, stop
using the local one.

### 7.3. Install it as a systemd service

This repo includes a template unit file at `deploy/truth-or-ban.service`.
Copy it and edit the placeholders (`youruser` and the project path) to
match your VPS:

```bash
sudo cp deploy/truth-or-ban.service /etc/systemd/system/truth-or-ban.service
sudo nano /etc/systemd/system/truth-or-ban.service   # fix User/WorkingDirectory/paths
sudo systemctl daemon-reload
sudo systemctl enable truth-or-ban    # start automatically on boot
sudo systemctl start truth-or-ban
```

### 7.4. Manage and monitor it

```bash
sudo systemctl status truth-or-ban    # is it running?
sudo systemctl restart truth-or-ban   # after pulling code updates
sudo systemctl stop truth-or-ban
journalctl -u truth-or-ban -f         # follow logs live
journalctl -u truth-or-ban -n 100     # last 100 log lines
```

Since `Restart=on-failure` is set, `systemd` will automatically restart
the bot if it ever crashes, and it'll start on its own if the VPS
reboots.

### 7.5. Updating after a code change

```bash
cd /home/youruser/truth-or-ban
git pull
source .venv/bin/activate
pip install -r requirements.txt   # only needed if dependencies changed
sudo systemctl restart truth-or-ban
```

import html


def display_name(
    user_id: int,
    first_name: str | None,
    last_name: str | None,
    username: str | None,
) -> str:
    """Always shows the person's name rather than @username. For anyone
    imported via the Telethon script who hasn't posted yet, this can
    reflect the importing account's saved contact name rather than the
    person's real profile name - a Telegram API quirk, not something we
    control - but it self-corrects the moment they send a real message,
    since the live bot always overwrites the stored name from Bot API
    updates (which are never contact-tainted).
    """
    name = " ".join(p for p in (first_name, last_name) if p).strip()
    return name or username or f"User {user_id}"


def mention_html(user_id: int, name: str) -> str:
    """A mention that notifies the user even if they have no username."""
    return f'<a href="tg://user?id={user_id}">{html.escape(name)}</a>'

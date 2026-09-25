import html


def display_name(
    user_id: int,
    first_name: str | None,
    last_name: str | None,
    username: str | None,
) -> str:
    """Prefers @username over first/last name: a username is stable and
    always accurate, while first/last name can be stale (unposted since a
    name change) or, for anyone imported via the Telethon script, reflect
    the importing account's saved contact name rather than the person's
    real profile name - a Telegram API quirk, not something we control.
    """
    if username:
        return f"@{username}"
    name = " ".join(p for p in (first_name, last_name) if p).strip()
    return name or f"User {user_id}"


def mention_html(user_id: int, name: str) -> str:
    """A mention that notifies the user even if they have no username."""
    return f'<a href="tg://user?id={user_id}">{html.escape(name)}</a>'

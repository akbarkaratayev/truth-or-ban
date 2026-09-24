import html


def display_name(
    user_id: int,
    first_name: str | None,
    last_name: str | None,
    username: str | None,
) -> str:
    name = " ".join(p for p in (first_name, last_name) if p).strip()
    return name or username or f"User {user_id}"


def mention_html(user_id: int, name: str) -> str:
    """A mention that notifies the user even if they have no username."""
    return f'<a href="tg://user?id={user_id}">{html.escape(name)}</a>'

import html

CHUNK_CHAR_LIMIT = 3500


def format_history(entries: list[dict]) -> list[str]:
    """Formats answered Q&A entries into one or more messages, respecting
    Telegram's message length limit. Returns an empty list if there are no
    entries, letting the caller decide the "nothing here" wording.
    """
    if not entries:
        return []

    lines: list[str] = []
    for i, entry in enumerate(entries, start=1):
        date_asked = entry["date_asked"][:10]
        lines.append(
            f"{i}. <b>Q:</b> {html.escape(entry['question'])} <i>({date_asked})</i>"
        )
        lines.append(f"   <b><i>{html.escape(entry['answer'])}</i></b>")
        lines.append("")

    return _chunk_lines(lines)


def _chunk_lines(lines: list[str], limit: int = CHUNK_CHAR_LIMIT) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1
        if current and current_len + line_len > limit:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks

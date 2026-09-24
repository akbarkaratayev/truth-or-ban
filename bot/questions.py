from pathlib import Path


def load_questions(path: str) -> list[str]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    lines = file_path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]

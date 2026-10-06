"""Заметки сохраняются в notes.txt рядом с программой."""
from pathlib import Path
from datetime import datetime

NOTES_FILE = Path(__file__).resolve().parent.parent / "notes.txt"

def add_note(text: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {text}\n")

def read_notes() -> str:
    if not NOTES_FILE.exists():
        return "Пока пусто..."
    return NOTES_FILE.read_text(encoding="utf-8")

def clear_notes() -> None:
    if NOTES_FILE.exists():
        NOTES_FILE.unlink()
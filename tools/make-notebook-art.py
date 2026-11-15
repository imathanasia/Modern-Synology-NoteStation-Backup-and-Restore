#!/usr/bin/env python3
"""Generate three optional no-cat ANSI terminal banners for NoteStation Backup."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = "\033["
CYAN = "101;244;255"
PINK = "255;95;178"
YELL = "255;230;109"
GREE = "114;241;163"
PURP = "189;140;255"
DIM = "145;134;170"
WHITE = "255;244;255"


def c(color: str, text: str) -> str:
    return f"{E}38;2;{color}m{text}{E}0m"


def row(width: int, *parts: tuple[str, str]) -> str:
    """Wrap colored (text, color) segments in a fixed visible-width box row."""
    visible = "".join(text for text, _ in parts)
    pad = " " * max(0, width - len(visible))
    body = "".join(c(color, text) for text, color in parts)
    return c(CYAN, "│") + body + pad + c(CYAN, "│")


def border(width: int, left: str, right: str) -> str:
    return c(CYAN, left + "─" * width + right)


def notebook() -> str:
    w = 34
    sep = ("  " + "─" * 26, DIM)
    rows = [
        row(w, ("", WHITE)),
        row(w, ("  ○  ○  ○  ○  ○  ○  ○  ○  ○", PURP)),
        row(w, sep),
        row(w, ("  NoteStation Backup", GREE)),
        row(w, sep),
        row(w, ("  ", WHITE), ("[x]", YELL), (" notebooks   ", WHITE), ("[x]", YELL), (" notes", WHITE)),
        row(w, ("  ", WHITE), ("[x]", YELL), (" tags        ", WHITE), ("[x]", YELL), (" files", WHITE)),
        row(w, sep),
        row(w, ("  daily · keep 7 · verified", PINK)),
        row(w, ("", WHITE)),
    ]
    return "\n".join([
        c(DIM, "  spiral-bound notebook"),
        "  " + border(w, "╭", "╮"),
        *["  " + r for r in rows],
        "  " + border(w, "╰", "╯"),
    ])


def stack() -> str:
    return "\n".join([
        c(DIM, "  stacked backup notes"),
        c(PURP, "      ┌─────────────────────┐"),
        c(PURP, "     ┌─────────────────────┐│"),
        c(CYAN, "    ┌─────────────────────┐││"),
        c(CYAN, "    │") + " " + c(GREE, "✓") + c(WHITE, "  content.tgz") + "      " + c(PURP, "│││"),
        c(CYAN, "    │") + " " + c(GREE, "✓") + c(WHITE, "  index.dump") + "       " + c(PURP, "│││"),
        c(CYAN, "    │") + " " + c(GREE, "✓") + c(WHITE, "  notes.txt") + "        " + c(PURP, "│││"),
        c(CYAN, "    └─────────────────────┘") + c(PURP, "││"),
        c(PURP, "     └─────────────────────┘│"),
        c(PURP, "      └─────────────────────┘"),
    ])


def folder() -> str:
    w = 34
    rows = [
        row(w, ("  NOTESTATION / BACKUP", GREE)),
        border(w, "├", "┤"),
        row(w, ("  ", WHITE), ("✓", GREE), ("  NoteStation_data.tgz", WHITE)),
        row(w, ("  ", WHITE), ("✓", GREE), ("  notestation_pg.dump", WHITE)),
        row(w, ("  ", WHITE), ("✓", GREE), ("  notestation_list.txt", WHITE)),
    ]
    return "\n".join([
        c(DIM, "  archive folder"),
        "  " + border(w, "╭", "╮"),
        *["  " + r for r in rows],
        "  " + border(w, "╰", "╯"),
    ])


def main() -> None:
    for name, fn in (
        ("avatar-notebook-plain.ansi", notebook),
        ("avatar-notes-stack.ansi", stack),
        ("avatar-archive.ansi", folder),
    ):
        (ROOT / name).write_text(fn() + "\n", encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()

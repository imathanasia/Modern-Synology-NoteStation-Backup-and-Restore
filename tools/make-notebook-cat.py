#!/usr/bin/env python3
"""Create an optional ANSI cat-with-notebook banner for CLI preview."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = "\033["
PINK = "255;95;178"
CYAN = "101;244;255"
WHITE = "255;244;255"
YELLOW = "255;230;109"


def paint(color: str, text: str) -> str:
    return f"{E}38;2;{color}m{text}{E}0m"


def main() -> None:
    lines = [paint(CYAN, "  NoteStation Backup · notes keeper")]
    for i, color in enumerate(("255;95;95", "255;169;77", YELLOW, "125;255;155", "101;232;255", "189;140;255")):
        lines.append(paint(color, "=" * (10 + i * 2)))
    lines.extend([
        paint(WHITE, "        /\\_/\\"),
        paint(CYAN, "       ( o.o )") + "    " + paint(YELLOW, "+---------+"),
        paint(WHITE, "        > ^ <") + "    " + paint(YELLOW, "|  NOTES  |"),
        paint(PINK, "      __/| |\\__") + "   " + paint(YELLOW, "|  [::]   |"),
        paint(PINK, "     /___|_|___\\") + "  " + paint(YELLOW, "+---------+"),
        paint(CYAN, "       /_/ \\_\\") + "      " + paint(WHITE, "safe copies, happy cat"),
    ])
    (ROOT / "avatar-notebook.ansi").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote avatar-notebook.ansi")


if __name__ == "__main__":
    main()

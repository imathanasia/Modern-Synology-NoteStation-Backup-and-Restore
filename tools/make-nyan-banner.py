#!/usr/bin/env python3
"""Create an optional, playful ANSI cat banner for terminal preview."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ESC = "\033["
RAINBOW = ["255;95;95", "255;169;77", "255;230;109", "125;255;155", "101;232;255", "189;140;255"]
WHITE = "255;244;255"
PINK = "255;95;178"
CYAN = "101;244;255"
ROWS = [
    "        /\\_/\\        ",
    "       ( o.o )       ",
    "        > ^ <        ",
    "    ___/     \\___    ",
    "   /=============\\   ",
    "  |==o===o===o====|  ",
    "  |===o===o===o===|  ",
    "   \\=============/   ",
    "     /_/     \\_\\     ",
]


def main() -> None:
    lines = [f"{ESC}38;2;{CYAN}m  NoteStation Backup · optional terminal cat{ESC}0m"]
    for band, color in enumerate(RAINBOW):
        lines.append(f"{ESC}38;2;{color}m" + "=" * (12 + band * 2) + f"{ESC}0m")
    for row_index, row in enumerate(ROWS):
        color = CYAN if row_index == 1 else PINK if row_index in (4, 5, 6, 7) else WHITE
        lines.append(f"{ESC}38;2;{color}m{row}{ESC}0m")
    lines.append(f"{ESC}38;2;{RAINBOW[0]}m      ·{ESC}38;2;{RAINBOW[1]}m·{ESC}38;2;{RAINBOW[2]}m·{ESC}38;2;{RAINBOW[3]}m·{ESC}38;2;{RAINBOW[4]}m·{ESC}38;2;{RAINBOW[5]}m·{ESC}0m")
    (ROOT / "avatar-nyan.ansi").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote avatar-nyan.ansi")


if __name__ == "__main__":
    main()

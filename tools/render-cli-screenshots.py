#!/usr/bin/env python3
"""Capture safe CLI screens and render them with headless Chromium.

Examples:
  python3 tools/render-cli-screenshots.py
  CHROME_BIN=/path/to/chrome python3 tools/render-cli-screenshots.py
"""
from __future__ import annotations

import html
import os
import pty
import re
import select
import struct
import subprocess
import termios
import time
import tty
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "notes-backup.sh"
OUT = ROOT / "docs" / "screenshots"
CHROME = os.environ.get("CHROME_BIN", "/root/.cache/ms-playwright/chromium-1254/chrome-linux64/chrome")
SGR = re.compile(r"\x1b\[([0-9;]*)m")
OTHER_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def capture(args: list[str], send_quit: bool = False, avatar_file: Path | None = None) -> str:
    master, slave = pty.openpty()
    termios.tcsetwinsize(slave, (38, 100))
    env = dict(os.environ, TERM="xterm-256color", COLUMNS="100", LINES="38")
    env["DEST_DIR"] = "/var/services/homes/<NoteStation-owner>/NoteStationBackup"
    if args == ["menu"]:
        env["AVATAR_FILE"] = str(avatar_file or ROOT / "avatar-nyan.ansi")
    proc = subprocess.Popen(["sh", str(SCRIPT), *args], stdin=slave,
                            stdout=slave, stderr=slave, cwd=ROOT, env=env,
                            close_fds=True)
    os.close(slave)
    output = bytearray()
    quit_sent = False
    while True:
        ready, _, _ = select.select([master], [], [], 0.1)
        if ready:
            try:
                block = os.read(master, 65536)
            except OSError:
                block = b""
            if not block:
                break
            output.extend(block)
            if send_quit and not quit_sent and b"choice:" in output:
                os.write(master, b"0\n")
                quit_sent = True
        if proc.poll() is not None and not ready:
            break
    os.close(master)
    proc.wait(timeout=5)
    text = output.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "")
    return text


def color(css_parts: list[str]) -> str:
    return ";".join(css_parts)


def ansi_html(text: str) -> str:
    fg = None
    bg = None
    bold = False
    pieces: list[str] = []
    pos = 0

    def start_span() -> str:
        styles = []
        if fg:
            styles.append(f"color:{fg}")
        if bg:
            styles.append(f"background-color:{bg}")
        if bold:
            styles.append("font-weight:700")
        return f'<span style="{color(styles)}">' if styles else ""

    for match in SGR.finditer(text):
        if match.start() > pos:
            piece = text[pos:match.start()]
            pieces.append(start_span() + html.escape(piece).replace("\n", "<br>") + ("</span>" if fg or bg or bold else ""))
        values = [int(v) for v in match.group(1).split(";") if v] or [0]
        i = 0
        while i < len(values):
            value = values[i]
            if value == 0:
                fg = bg = None
                bold = False
            elif value == 1:
                bold = True
            elif value == 22:
                bold = False
            elif value in (38, 48) and i + 4 < len(values) and values[i + 1] == 2:
                rgb = f"rgb({values[i + 2]},{values[i + 3]},{values[i + 4]})"
                if value == 38:
                    fg = rgb
                else:
                    bg = rgb
                i += 4
            i += 1
        pos = match.end()
    if pos < len(text):
        piece = OTHER_ESCAPE.sub("", text[pos:])
        pieces.append(start_span() + html.escape(piece).replace("\n", "<br>") + ("</span>" if fg or bg or bold else ""))
    rendered = "".join(pieces)
    rendered = OTHER_ESCAPE.sub("", rendered)
    return rendered


def screenshot(name: str, title: str, args: list[str], send_quit: bool = False,
               avatar_file: Path | None = None) -> None:
    terminal = ansi_html(capture(args, send_quit=send_quit, avatar_file=avatar_file))
    page = f'''<!doctype html><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;padding:34px;background:#100c1d;color:#e9e4f2;
font:15px/1.32 "Cascadia Code","SFMono-Regular",Menlo,Consolas,monospace}}
.window{{width:max-content;max-width:100%;margin:auto;border:1px solid #4e4565;border-radius:13px;
background:#120d20;box-shadow:0 20px 70px #0009;overflow:hidden}}
.bar{{height:38px;background:#1a1429;border-bottom:1px solid #3b3150;padding:10px 15px;color:#9186aa}}
.dots{{color:#ff5fb2;letter-spacing:4px}}.caption{{margin-left:14px}}
pre{{margin:0;padding:20px 24px 24px;white-space:pre;font:14px/1.05 "Cascadia Code","SFMono-Regular",Menlo,Consolas,monospace;min-width:750px}}
</style><div class="window"><div class="bar"><span class="dots">● ● ●</span><span class="caption">NoteStation Backup · {html.escape(title)}</span></div><pre>{terminal}</pre></div>'''
    html_path = OUT / f"{name}.html"
    png_path = OUT / f"{name}.png"
    html_path.write_text(page, encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu",
                    "--disable-dev-shm-usage", "--hide-scrollbars",
                    "--window-size=1120,900", f"--screenshot={png_path}",
                    html_path.as_uri()], check=True, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
    print(f"wrote {png_path}")


def main() -> None:
    if not SCRIPT.is_file():
        raise SystemExit(f"missing CLI script: {SCRIPT}")
    if not Path(CHROME).is_file():
        raise SystemExit(f"Chromium not found at {CHROME}; set CHROME_BIN")
    OUT.mkdir(parents=True, exist_ok=True)
    screenshot("menu", "Interactive menu", ["menu"], send_quit=True)
    screenshot("notebook-cat", "Notebook cat option", ["menu"], send_quit=True,
               avatar_file=ROOT / "avatar-notebook.ansi")
    screenshot("help", "CLI help", ["help"])


if __name__ == "__main__":
    main()

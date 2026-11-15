#!/usr/bin/env python3
"""Build a single local HTTP preview page for terminal-art options and NAS status."""
from __future__ import annotations

import html
import importlib.util
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVE = Path("/root/projects/serve/notestation-art")
RENDER = ROOT / "tools" / "render-cli-screenshots.py"

spec = importlib.util.spec_from_file_location("cli_render", RENDER)
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)

ART = [
    ("Spiral notebook", "avatar-notebook-plain.ansi", "Ring-bound notebook with a verified backup checklist. No cat."),
    ("Stacked note cards", "avatar-notes-stack.ansi", "Layered note cards carrying the three backup artifacts."),
    ("Archive folder", "avatar-archive.ansi", "A file folder containing verified content, index and note list."),
    ("Rainbow cat", "avatar-nyan.ansi", "The optional playful cat banner."),
    ("Notebook cat", "avatar-notebook.ansi", "Cat with a notebook, for the trolls."),
    ("GitHub identicon", "avatar.ansi", "Current default: your GitHub avatar as truecolor ANSI."),
]

STATUS = [
    ("Tool path", "/volume1/homes/&lt;owner&gt;/notebackup/notes-backup.sh", "Deployed"),
    ("Scripts", "notes-backup.sh, restore-notes.sh, export-notes.sh", "Present"),
    ("Banner files", "avatar.ansi, avatar-nyan.ansi, avatar-notebook.ansi", "Present"),
    ("CLI preview", "sh notes-backup.sh preview", "rc=0, no data changed"),
    ("Backups on NAS", "4 archives + pg dumps + note lists", "Validated earlier"),
    ("Daily DSM task", "No NoteStation Backup entry in synoschedtask --get", "NOT created yet"),
]


def card(title: str, filename: str, description: str) -> str:
    ansi = (ROOT / filename).read_text(encoding="utf-8")
    cmd = f'AVATAR_FILE=/path/to/{filename} sh notes-backup.sh preview'
    return f'''<section class="card">
  <h2>{html.escape(title)}</h2>
  <p>{html.escape(description)}</p>
  <div class="window"><div class="bar"><span class="dots">● ● ●</span> {html.escape(filename)}</div><pre>{render.ansi_html(ansi)}</pre></div>
  <code>{html.escape(cmd)}</code>
</section>'''


def main() -> None:
    SERVE.mkdir(parents=True, exist_ok=True)
    for png in (ROOT / "docs" / "screenshots").glob("*.png"):
        shutil.copy2(png, SERVE / png.name)
    for _, filename, _ in ART:
        shutil.copy2(ROOT / filename, SERVE / filename)
    cards = "\n".join(card(*item) for item in ART)
    rows = "\n".join(
        f"<tr><td>{html.escape(k)}</td><td>{v}</td><td class=\"{('bad' if 'NOT' in s or 'NOT ' in s else 'good')}\">{html.escape(s)}</td></tr>"
        for k, v, s in STATUS
    )
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<title>NoteStation Backup · terminal art preview</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;padding:34px;background:#100c1d;color:#e9e4f2;font:15px/1.45 "Cascadia Code","SFMono-Regular",Menlo,Consolas,monospace}}
header{{max-width:1200px;margin:0 auto 26px}}h1{{margin:0;color:#72f1a3}}h2{{margin:0 0 6px;color:#65f4ff;font-size:17px}}
p{{margin:0 0 12px;color:#9186aa}}.intro{{color:#c9c0d8}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px;max-width:1200px;margin:auto}}
.card{{border:1px solid #3b3150;border-radius:12px;background:#120d20;padding:16px}}
.window{{border:1px solid #3b3150;border-radius:9px;overflow:hidden;margin-bottom:10px}}
.bar{{background:#1a1429;padding:8px 12px;color:#9186aa;font-size:13px}}.dots{{color:#ff5fb2;letter-spacing:3px}}
pre{{margin:0;padding:14px;white-space:pre;overflow:auto;font:13px/1.05 "Cascadia Code","SFMono-Regular",Menlo,Consolas,monospace}}
code{{display:block;background:#1a1429;padding:9px;border-radius:6px;color:#ffe66d;font-size:12px;overflow:auto}}
.status{{max-width:1200px;margin:28px auto;border:1px solid #3b3150;border-radius:12px;padding:16px;background:#120d20}}
table{{width:100%;border-collapse:collapse}}td{{padding:8px;border-bottom:1px solid #2c2440;font-size:13px}}td:first-child{{color:#65f4ff}}
.good{{color:#72f1a3}}.bad{{color:#ff5fb2;font-weight:700}}
a{{color:#65f4ff}}.shots{{max-width:1200px;margin:22px auto;color:#9186aa}}
</style>
<header><h1>NoteStation Backup · terminal art</h1>
<p class="intro">Six banner options. The first three are no-cat proposals. Each card includes the exact preview command. Nothing on this page changes the NAS.</p></header>
<div class="grid">{cards}</div>
<section class="status"><h2>NAS verification</h2><table>{rows}</table>
<p style="margin-top:12px">To schedule daily: DSM → Control Panel → Task Scheduler → Create → Scheduled Task → User-defined script (root), then run <code style="margin-top:8px">sh /path/to/notes-backup.sh backup</code></p></section>
<p class="shots">Existing CLI screenshots: <a href="menu.png">menu</a> · <a href="notebook-cat.png">notebook cat</a> · <a href="help.png">help</a></p>
</html>'''
    (SERVE / "index.html").write_text(page, encoding="utf-8")
    print(SERVE / "index.html")


if __name__ == "__main__":
    main()

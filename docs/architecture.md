# NoteStation on DSM 7.4.1 (<NAS_IP>) — live architecture findings

Verified 2026-11-15 via read-only SSH as root (key auth works).

## Storage layout (the important discovery)
- Index is **PostgreSQL**, not SQLite: DBs `notestation` + `synodrive`,
  user `NoteStation`, via pgbouncer (`/volume1/@appstore/NoteStation/etc/pgbouncer.ini`).
  Postgres socket: `/var/run/postgresql`, `psql` at `/usr/bin/psql`.
- Note content: `/volume1/@SynoDrive/NoteStation/<object_id>/` — 194 dirs, 26 MB.
  - `<object_id>` = `<USER_UID>_<token>` where **<USER_UID> = <USER>'s uid** (same scheme as .nsx).
  - Per-note dir: `basic.json` (times, `parent_id` = notebook object_id),
    `metatext.json`, `git_info.json`, and dirs:
    - `version/text/` — **plain-text JSON fields with base64-of-field-name filenames**
      (e.g. `Y29udGVudA==` = `content` → note body as a JSON string, HTML/NS format;
      `YXR0YWNobWVudA==` = `attachment` → JSON index with `md5`/`ref`/`name`/`ctime`,
      same ref scheme as .nsx; `YnJlZg==` = `brief`; `ZW5jcnlwdGVk`; `title`; `tags`...).
      Content itself is **unencrypted JSON text** — directly parseable by our converter.
    - `version/.git/` — notes are git-versioned internally.
    - `metabinary/` — per-attachment blobs, base64-named.
- DB schema (`notestation` DB, public): `note` (object_id PK, title, brief, parent_id,
  tag json, attachment json, encrypt, recycle, ctime/mtime...), `notebook`, `stack`,
  `tag`, `tag_note`, `todo`, `link`, `smart`, `note_encrypt`, perms, shortcuts.
- Row counts: 191 notes, 3 notebooks, 1 tag, 0 stacks, 0 todos.

## CLI export paths (package tools: /var/packages/NoteStation/target/tools/)
- `synosnote` is **`synonsnote`** and it is a full per-note CLI:
  - `--list <requester=UID> [filter/offset/limit/field/sort_by/sort_direction]`
    (requester = numeric uid, e.g. <USER_UID> for <USER>; NOT the username)
  - `--get <requester> <object_id> [<ver>]`
  - `--download <requester> <object_id> <file_id> <format> [<ver> <filename>]`
  - `--create/--set/--delete` (write ops — avoid)
- `synonsimport` — only evernote resume; `synonsconvert --index` — reindex only.
- `synopkg` full path: `/usr/syno/bin/synopkg` (NOT in sbin; PATH differs in non-login shell).
- DSM CLI facts: `/usr/syno/sbin/synouser` and `synogroup` exist;
  **`synoservice` does not exist** on 7.4.1 (only `synoservicemigrate`).

## Package app facts
- App: ports 9350 (http)/9351 (https), `index.cgi`, root `/usr/syno/synoman`.
- Status: running (`/usr/syno/bin/synopkg status NoteStation`).
- Built-in cron: `/var/packages/NoteStation/target/tools/synonscrond --weekly_clean`.
- AppArmor profiles, import/evernote dir, feasibilitycheck scripts present.

## Export/backup routes (ranked)
1. **Filesystem copy** (best for full-fidelity backup): tar
   `/volume1/@SynoDrive/NoteStation` + `pg_dump notestation` (stop app not strictly
   required for read; optional `synopkg stop NoteStation` for consistency).
2. **CLI per-note export**: `synonsnote --list requester=<USER_UID>` to enumerate, then
   `--get`/`--download` per note (nice for selective/note-level export).
3. **Official**: Hyper Backup (DSM UI) or webapi .nsx export.

## Gotchas
- Non-interactive SSH (ash): `synopkg` not on PATH → use `/usr/syno/bin/synopkg`.
- Attachments: blobs live in note dir `metabinary/` (+ maybe @SynoDrive elsewhere);
  attachment JSON names are base64 field names, `ls` output may show odd escapes.
- Host IP of this agent server changed: now **<AGENT_IP>** (was .22).

## First run (2026-11-15 13:21 UTC) — verified
`sh /volume1/homes/<USER>/notebackup/export-notes.sh` as root, no app stop, rc=0:
- `NoteStation_data_20261115_142139.tgz` 2.2 MB — `gzip -t` OK, 10,403 entries
  (`NoteStation/<object_id>/...`).
- `notestation_pg_20261115_142139.dump` 61 KB — `pg_dump -Fc`, magic `PGDMP`.
- `notestation_list_20261115_142139.txt` 102 KB — full `synonsnote --list requester=<USER_UID>`.
- `last_backup.log` records `rc=0 data=26M`.
Retention (keep newest 7) is in-script (`KEEP=7`).

DSM Task Scheduler (Control Panel → Task Scheduler → Create → Scheduled Task →
User-defined script, Run as root, daily): command
`sh /volume1/homes/<USER>/notebackup/export-notes.sh >> /volume1/homes/<USER>/notebackup/task.log 2>&1`

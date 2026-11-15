#!/bin/sh
# Backup Synology NoteStation: content tree + PostgreSQL index dump (+ optional CLI list).
# Defaults are read-only w.r.t. the app (no stop/start). Run as root.
# Env overrides: DEST_DIR, PG_BIN, STOP_APP=1 (adds stop/start), PGDUMP_NAME
set -u
DATA=/volume1/@SynoDrive/NoteStation
if [ -z "${DEST_DIR:-}" ]; then
  FIRST=$(ls -d "$DATA"/*_* 2>/dev/null | head -1)
  OWNER=$(stat -c %U "$FIRST" 2>/dev/null)
  [ -n "$OWNER" ] || { echo "cannot identify NoteStation owner; set DEST_DIR explicitly" >&2; exit 1; }
  HOME_DIR="/var/services/homes/$OWNER"
  [ -d "$HOME_DIR" ] || HOME_DIR="/volume1/homes/$OWNER"
  [ -d "$HOME_DIR" ] || { echo "cannot resolve NoteStation owner's home; set DEST_DIR" >&2; exit 1; }
  DEST_DIR="$HOME_DIR/NoteStationBackup"
fi
STAMP=$(date +%Y%m%d_%H%M%S)
PGDUMP_NAME="${PGDUMP_NAME:-notestation_pg_${STAMP}.dump}"
CLI_USER="${CLI_USER:-}"
if [ -z "$CLI_USER" ]; then
  FIRST=$(ls -d "$DATA"/*_* 2>/dev/null | head -1)
  OBJECT=${FIRST##*/}
  CLI_USER=${OBJECT%%_*}
fi

mkdir -p "$DEST_DIR" || { echo "cannot create $DEST_DIR" >&2; exit 1; }

stopped=0
if [ "${STOP_APP:-0}" = "1" ]; then
  /usr/syno/bin/synopkg stop NoteStation >/dev/null 2>&1 && stopped=1
fi

rc=0
tar -czf "$DEST_DIR/NoteStation_data_${STAMP}.tgz" -C /volume1/@SynoDrive NoteStation || rc=$?
[ -x /usr/bin/pg_dump ] && /usr/bin/pg_dump -h /var/run/postgresql -U postgres -Fc \
  -f "$DEST_DIR/$PGDUMP_NAME" notestation || rc=$rc$?

if [ -n "$CLI_USER" ]; then
  /var/packages/NoteStation/target/tools/synonsnote --list "requester=$CLI_USER" \
    > "$DEST_DIR/notestation_list_${STAMP}.txt" 2>&1 || rc=$rc$?
fi

[ "$stopped" = "1" ] && /usr/syno/bin/synopkg start NoteStation >/dev/null 2>&1

echo "$(date -u +%FT%TZ) rc=$rc data=$(du -sh "$DATA" 2>/dev/null | cut -f1)" >> "$DEST_DIR/last_backup.log"

# Retention: keep the newest 7 of each artifact family
KEEP="${KEEP:-7}"
for pat in "NoteStation_data_*.tgz" "notestation_pg_*.dump" "notestation_list_*.txt"; do
  ls -t "$DEST_DIR"/$pat 2>/dev/null | tail -n +$((KEEP + 1)) | while read -r f; do
    rm -f "$f"; echo "retention: removed $(basename "$f")" >> "$DEST_DIR/last_backup.log"
  done
done

ls -lh "$DEST_DIR" | tail -8
exit "$rc"

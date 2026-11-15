#!/bin/sh
# Read-only recon of Synology NoteStation storage (DSM 7.4.x).
# Usage: sh recon-notestation.sh
set -u
APP=/volume1/@appstore/NoteStation
DATA=/volume1/@SynoDrive/NoteStation
TOOLS=/var/packages/NoteStation/target/tools

echo "== package status:"; /usr/syno/bin/synopkg status NoteStation 2>&1 | head -2
echo "== content dir:"; [ -d "$DATA" ] && echo "exists, $(ls "$DATA" | wc -l) objects, $(du -sh "$DATA" | cut -f1)"
echo "== sample note dir:"; for d in "$DATA"/*_*; do ls -la "$d" | head -8; break; done
echo "== version/text sample:"; for d in "$DATA"/*_*; do ls -la "$d/version/text" 2>/dev/null | head -8; break; done
echo "== app dirs:"; ls "$APP" 2>/dev/null
echo "== tools:"; ls "$TOOLS" 2>/dev/null | head -30
echo "== pgbouncer dbs:"; grep -E '^\[' /volume1/@appstore/NoteStation/etc/pgbouncer.ini 2>/dev/null | head -5
echo "== db tables:"; psql -h /var/run/postgresql -U postgres -d notestation -tAc "SELECT tablename FROM pg_tables WHERE schemaname='public'" 2>&1 | head -25
echo "== counts:"; psql -h /var/run/postgresql -U postgres -d notestation -tAc "SELECT (SELECT count(*) FROM note) AS notes, (SELECT count(*) FROM notebook) AS notebooks, (SELECT count(*) FROM tag) AS tags" 2>&1
echo "== cli list sample:"; FIRST=$(ls -d "$DATA"/*_* 2>/dev/null | head -1); OBJECT=${FIRST##*/}; UID=${OBJECT%%_*}; echo "requester uid=$UID"
[ -n "${UID:-}" ] && "$TOOLS/synonsnote" --list "requester=$UID" limit=2 2>&1 | head -14

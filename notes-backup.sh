#!/bin/sh
# notes-backup.sh — NoteStation backup / restore / sync for Synology DSM 7.x
# Author: ImAthanasia <https://github.com/ImAthanasia> · MIT
# No external deps; BusyBox ash safe.
set -u

VERSION="1.1.0"
AUTHOR="ImAthanasia"
REPO="https://github.com/imathanasia/Modern-Synology-NoteStation-Backup-and-Restore"

DATA_ROOT=/volume1/@SynoDrive
DATA="$DATA_ROOT/NoteStation"
TOOLS=/var/packages/NoteStation/target/tools
PG_DUMP=/usr/bin/pg_dump
PG_RESTORE=/usr/bin/pg_restore
resolve_home_destination() {
  first=$(ls -d "$DATA"/*_* 2>/dev/null | head -1)
  [ -n "$first" ] || return 1
  owner=$(stat -c %U "$first" 2>/dev/null)
  [ -n "$owner" ] || return 1
  for home_base in /var/services/homes /volume1/homes; do
    if [ -d "$home_base/$owner" ]; then
      printf '%s/NoteStationBackup' "$home_base/$owner"
      return 0
    fi
  done
  return 1
}
if [ -n "${DEST_DIR:-}" ]; then
  DEST_DIR=$DEST_DIR
else
  DEST_DIR=$(resolve_home_destination 2>/dev/null) || DEST_DIR=""
fi
KEEP="${KEEP:-7}"
BRIDGE="${BRIDGE:-http://127.0.0.1:8000}"
CLI_USER="${CLI_USER:-}"
AVATAR_FILE="${AVATAR_FILE:-$(dirname "$0")/avatar.ansi}"
LOG="${DEST_DIR:+$DEST_DIR/last_backup.log}"

# ---- palette (truecolor) / plain fallback when not a TTY ----
if [ -t 1 ] && [ -n "${TERM:-}" ] && [ "$TERM" != "dumb" ]; then
  ESC=$(printf '\033')
  PINK="${ESC}[38;2;255;95;178m"; CYAN="${ESC}[38;2;101;244;255m"
  YELL="${ESC}[38;2;255;230;109m"; GREE="${ESC}[38;2;114;241;163m"
  PURP="${ESC}[38;2;189;140;255m"; DIMC="${ESC}[38;2;145;134;170m"
  BOLD="${ESC}[1m"; RST="${ESC}[0m"
else
  PINK=; CYAN=; YELL=; GREE=; PURP=; DIMC=; BOLD=; RST=
fi

hr()    { printf '%s\n' "${DIMC}────────────────────────────────────────────────────────${RST}"; }
step()  { printf '%s▸ %s%s\n' "$CYAN" "$*" "$RST"; }
ok()    { printf '%s✓ %s%s\n' "$GREE" "$*" "$RST"; }
warn()  { printf '%s! %s%s\n' "$YELL" "$*" "$RST"; }
die()   { printf '%s✗ %s%s\n' "$PINK" "$*" "$RST" >&2; exit 1; }
log()   { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG" 2>/dev/null || true; }

banner() {
  [ -f "$AVATAR_FILE" ] && cat "$AVATAR_FILE"
  printf '%s┌──────────────────────────────────────────────────────┐%s\n' "$BOLD$CYAN" "$RST"
  printf '%s│%s  %sNoteStation Backup%s  v%s  by %s%s%s%s │%s\n' "$BOLD$CYAN" "$RST" "$BOLD$GREE" "$RST" "$VERSION" "$PINK" "@$AUTHOR" "$RST" "$BOLD$CYAN" "$RST"
  printf '%s└──────────────────────────────────────────────────────┘%s\n' "$BOLD$CYAN" "$RST"
  hr
}

usage() {
  printf '%sNoteStation Backup%s v%s — usage:\n\n' "$BOLD$GREE" "$RST" "$VERSION"
  printf '  %sbackup%s              create a backup now (alias: --batch)\n' "$CYAN" "$RST"
  printf '  %srestore%s <tgz>       restore a backup (--with-db <dump> [--yes] [--dry-run])\n' "$CYAN" "$RST"
  printf '  %ssync%s                push the newest backup to the remote bridge\n' "$CYAN" "$RST"
  printf '  %sstatus%s              show configuration and last runs\n' "$CYAN" "$RST"
  printf '  %spreview%s             print the menu without waiting or changing data\n' "$CYAN" "$RST"
  printf '  %smenu%s                interactive menu (default when TTY)\n' "$CYAN" "$RST"
  printf '  %shelp%s                this text\n\n' "$CYAN" "$RST"
  printf 'env: DEST_DIR (auto: owner home/NoteStationBackup), KEEP (%s)\n' "$KEEP"
  printf '     BRIDGE (%s), CLI_USER (auto%s)\n' "$BRIDGE" "${CLI_USER:+, override $CLI_USER}"
  printf 'resolved destination: %s\n' "${DEST_DIR:-unresolved; set DEST_DIR}"
  printf 'repo: %s\n' "$REPO"
}

preflight() {
  [ -d "$DATA" ] || die "note content dir not found: $DATA"
  [ -x "$TOOLS/synonsnote" ] || die "synonsnote not found under $TOOLS"
  [ -n "$DEST_DIR" ] || die "could not resolve NoteStation owner's home; enable DSM User Home service or set DEST_DIR explicitly"
  mkdir -p "$DEST_DIR" 2>/dev/null || die "cannot create $DEST_DIR"
  [ -w "$DEST_DIR" ] || die "$DEST_DIR is not writable"
  [ -x "$PG_DUMP" ] || warn "pg_dump not found ($PG_DUMP) — index dump disabled"
  if [ -z "$CLI_USER" ]; then
    first=$(ls -d "$DATA"/*_* 2>/dev/null | head -1)
    object=${first##*/}
    CLI_USER=${object%%_*}
    case "$CLI_USER" in
      ''|*[!0-9]*) die "could not determine NoteStation requester uid; set CLI_USER=<numeric uid>" ;;
    esac
  fi
}

newest_backup() { ls -t "$DEST_DIR"/NoteStation_data_*.tgz 2>/dev/null | head -1; }

do_backup() {
  preflight
  stamp=$(date +%Y%m%d_%H%M%S)
  tgz="$DEST_DIR/NoteStation_data_${stamp}.tgz"
  dump="$DEST_DIR/notestation_pg_${stamp}.dump"
  list="$DEST_DIR/notestation_list_${stamp}.txt"
  rc=0

  step "packing note content ($DATA)"
  tar -czf "$tgz" -C "$DATA_ROOT" NoteStation || { rm -f "$tgz"; die "tar failed"; }

  if [ -x "$PG_DUMP" ]; then
    step "dumping PostgreSQL index"
    "$PG_DUMP" -h /var/run/postgresql -U postgres -Fc -f "$dump" notestation || { warn "pg_dump failed"; rc=3; }
  fi

  step "listing notes via CLI (requester=$CLI_USER)"
  "$TOOLS/synonsnote" --list "requester=$CLI_USER" > "$list" 2>&1 || { warn "note list failed"; rc=3; }

  gzip -t "$tgz" || { rm -f "$tgz"; die "archive verification failed"; }
  ok "archive verified: $(du -h "$tgz" | cut -f1)"

  step "retention: keeping newest $KEEP"
  for pat in "NoteStation_data_*.tgz" "notestation_pg_*.dump" "notestation_list_*.txt"; do
    ls -t "$DEST_DIR"/$pat 2>/dev/null | tail -n +$((KEEP + 1)) | while read -r f; do rm -f "$f"; done
  done

  log "backup rc=$rc tgz=$(basename "$tgz") data=$(du -sh "$DATA" 2>/dev/null | cut -f1)"
  printf '\n%sbackup:%s %s\n' "$GREE" "$RST" "$tgz"
  return $rc
}

do_restore() {
  tgz=""; db=""; yes=0; dry=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --with-db) db="${2:-}"; shift 2 || shift ;;
      --yes) yes=1; shift ;;
      --dry-run) dry=1; shift ;;
      -*) die "unknown option: $1" ;;
      *) [ -n "$tgz" ] && die "unexpected argument: $1"; tgz="$1"; shift ;;
    esac
  done
  [ -n "$tgz" ] || die "usage: notes-backup.sh restore <tgz> [--with-db <dump>] [--yes] [--dry-run]"
  [ -f "$tgz" ] || die "backup not found: $tgz"
  gzip -t "$tgz" || die "backup is not a valid gzip: $tgz"
  [ -z "$db" ] || [ -f "$db" ] || die "db dump not found: $db"
  [ -d "$DATA" ] || die "note content dir not found: $DATA"

  printf 'backup : %s (%s)\n' "$tgz" "$(du -h "$tgz" | cut -f1)"
  [ -n "$db" ] && printf 'db dump: %s (%s)\n' "$db" "$(du -h "$db" | cut -f1)"
  printf 'target : %s\n' "$DATA"
  if [ "$dry" = 1 ]; then
    ok "dry run — plan only, nothing changed"
    return 0
  fi
  if [ "$yes" != 1 ]; then
    printf 'stop NoteStation and restore? [y/N] '
    read -r a
    case "$a" in y|Y|yes|YES) ;; *) printf 'aborted\n'; return 0 ;; esac
  fi

  stamp=$(date +%Y%m%d_%H%M%S)
  stage="$DATA_ROOT/.NoteStation.restore.$stamp"
  old="$DATA_ROOT/.NoteStation.pre-restore.$stamp"
  mkdir -p "$stage" || die "cannot create stage dir"
  tar -xzf "$tgz" -C "$stage" || { rm -rf "$stage"; die "extract failed"; }
  [ -d "$stage/NoteStation" ] || { rm -rf "$stage"; die "archive has no NoteStation/ top level"; }

  step "stopping NoteStation"
  /usr/syno/bin/synopkg stop NoteStation >/dev/null 2>&1 || warn "stop returned nonzero"
  [ -d "$DATA" ] && mv "$DATA" "$old" || true
  if ! mv "$stage/NoteStation" "$DATA"; then
    warn "swap failed — rolling back"
    [ -d "$old" ] && mv "$old" "$DATA"
    rm -rf "$stage"
    /usr/syno/bin/synopkg start NoteStation >/dev/null 2>&1
    die "restore failed, previous content restored"
  fi
  rm -rf "$stage"

  if [ -n "$db" ] && [ -x "$PG_RESTORE" ]; then
    step "restoring PostgreSQL index"
    "$PG_RESTORE" -h /var/run/postgresql -U postgres -d notestation --clean --if-exists "$db" || warn "pg_restore reported errors"
  fi

  step "reindexing"
  "$TOOLS/synonsconvert" --index || warn "reindex reported errors"
  /usr/syno/bin/synopkg start NoteStation >/dev/null 2>&1 || warn "start returned nonzero"
  log "restore tgz=$(basename "$tgz") db=$( [ -n "$db" ] && basename "$db" || echo none )"
  ok "restored — previous content kept at $old"
}

do_sync() {
  preflight
  command -v curl >/dev/null 2>&1 || die "curl not found"
  f=$(newest_backup)
  [ -n "$f" ] || die "no backup to sync in $DEST_DIR"
  name=$(basename "$f")
  step "pushing $name ($(du -h "$f" | cut -f1)) → $BRIDGE/upload/$name"
  if curl -fsS --max-time 60 --data-binary "@$f" "$BRIDGE/upload/$name"; then
    ok "uploaded"
    log "sync ok $name"
  else
    warn "upload failed (bridge reachable?)"
    log "sync failed $name"
    return 1
  fi
  printf '%stip:%s keep %sDEST_DIR%s where Synology Drive mirrors it — a NAS-only backup dies with the NAS.\n' "$DIMC" "$RST" "$CYAN" "$RST"
}

do_status() {
  printf '%sNoteStation Backup%s v%s — status\n\n' "$BOLD$GREE" "$RST" "$VERSION"
  printf 'destination : %s\n' "${DEST_DIR:-unresolved; set DEST_DIR}"
  printf 'bridge      : %s\n' "$BRIDGE"
  printf 'note objects: %s\n' "$(ls "$DATA" 2>/dev/null | wc -l)"
  printf 'backups     : %s (keep %s)\n' "$(ls "$DEST_DIR"/NoteStation_data_*.tgz 2>/dev/null | wc -l)" "$KEEP"
  printf 'last run    : %s\n' "$(tail -1 "$LOG" 2>/dev/null)"
  ls -lh "$DEST_DIR" 2>/dev/null | tail -8
}

draw_menu() {
  printf '%sMenu%s\n' "$BOLD$CYAN" "$RST"
  printf '  %s1%s) backup now   %s2%s) restore   %s3%s) sync remote\n' "$GREE" "$RST" "$YELL" "$RST" "$PURP" "$RST"
  printf '  %s4%s) status       %s5%s) change destination   %s0%s) quit\n' "$CYAN" "$RST" "$PINK" "$RST" "$DIMC" "$RST"
  hr
}

preview() {
  banner
  draw_menu
  printf '%sPreview only — no action taken.%s\n' "$DIMC" "$RST"
}

menu() {
  banner
  while :; do
    draw_menu
    printf 'choice: '
    read -r c
    case "$c" in
      1) do_backup ;;
      2) f=$(newest_backup); [ -n "$f" ] && do_restore "$f" || warn "no backups in $DEST_DIR" ;;
      3) do_sync ;;
      4) do_status ;;
      5) printf 'destination [%s]: ' "$DEST_DIR"; read -r d; [ -n "$d" ] && DEST_DIR="$d" && LOG="$DEST_DIR/last_backup.log" ;;
      0|q|Q) printf '%sbye%s\n' "$GREE" "$RST"; exit 0 ;;
      *) warn "invalid choice" ;;
    esac
  done
}

cmd="${1:-}"
[ $# -gt 0 ] && shift
case "$cmd" in
  backup|--batch|-b) do_backup "$@" ;;
  restore|-r) do_restore "$@" ;;
  sync|-s) do_sync ;;
  status) do_status ;;
  preview|--preview) preview ;;
  menu|"") [ -t 0 ] && menu || usage ;;
  help|--help|-h) usage ;;
  *) usage; exit 2 ;;
esac

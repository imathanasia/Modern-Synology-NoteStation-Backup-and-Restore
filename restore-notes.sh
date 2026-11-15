#!/bin/sh
# Compatibility wrapper — the restore logic now lives in notes-backup.sh.
# Usage: sh restore-notes.sh <backup.tgz> [--with-db <dump>] [--yes] [--dry-run]
DIR=$(dirname "$0")
exec sh "$DIR/notes-backup.sh" restore "$@"

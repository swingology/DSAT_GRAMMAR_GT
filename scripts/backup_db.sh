#!/usr/bin/env bash
# Dumps the DSAT postgres DB via the running dsat-db Docker container.
# Keeps the 10 most recent dumps; older ones are pruned automatically.
# Safe to run while the DB is live — pg_dump uses a consistent snapshot.

set -euo pipefail

BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/backups"
CONTAINER="dsat-db"
DB_USER="dsat"
DB_NAME="dsat_dev"
KEEP=10

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTFILE="$BACKUP_DIR/dsat_dev_${TIMESTAMP}.dump"

echo "[$(date)] Starting backup → $OUTFILE"

if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "[$(date)] ERROR: container $CONTAINER not running — skipping backup" >&2
  exit 1
fi

docker exec "$CONTAINER" \
  pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$OUTFILE"

SIZE=$(du -sh "$OUTFILE" | cut -f1)
echo "[$(date)] Backup complete: $OUTFILE ($SIZE)"

# Prune old backups, keep $KEEP most recent. Sort by the timestamp encoded in
# the filename, not mtime — a git-tracked dump's mtime resets on checkout,
# which let stale dumps dodge rotation indefinitely (see .gitignore, dumps
# are no longer committed).
ls "$BACKUP_DIR"/dsat_dev_*.dump 2>/dev/null | sort -r | tail -n +$((KEEP + 1)) | while read -r old; do
  echo "[$(date)] Pruning old backup: $old"
  rm -f "$old"
done

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
mkdir -p backups
backup_stamp=$(date -u +%Y%m%dT%H%M%SZ)
docker compose --env-file .env.production -f compose.prod.yaml exec -T db \
  sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "backups/${backup_stamp}.dump"
docker compose --env-file .env.production -f compose.prod.yaml exec -T app \
  tar -cz -C /data/uploads . > "backups/${backup_stamp}-uploads.tar.gz"
echo "Backup salvo em backups/${backup_stamp}.*. Copie-o também para fora da VPS."

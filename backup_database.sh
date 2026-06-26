#!/bin/bash
set -euo pipefail

PATH="/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PATH

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-${SCRIPT_DIR}/.env}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-asrp_database}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE" >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

BACKUP_DATE=$(date -u +"%Y-%m-%d_%H-%M-%S_UTC")

BACKUP_BUCKET="${S3_BACKUP_BUCKET:-backups}"
BACKUP_DIR="${S3_BACKUP_DIR:-database_backups}"
BACKUP_FILENAME="${DB_NAME}_${BACKUP_DATE}.dump"

if [[ -z "${S3_ENDPOINT:-}" ]]; then
  echo "S3_ENDPOINT is required" >&2
  exit 1
fi

export AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$S3_SECRET_KEY"
export AWS_DEFAULT_REGION="${S3_REGION:-auto}"

docker exec \
  -e PGPASSWORD="$DB_PASSWORD" \
  "$POSTGRES_CONTAINER" \
  pg_dump \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -Fc \
  -Z 6 \
  --no-owner \
  --no-acl \
| aws s3 cp - "s3://${BACKUP_BUCKET}/${BACKUP_DIR}/${BACKUP_FILENAME}" --endpoint-url "$S3_ENDPOINT"

echo "Backup uploaded: s3://${BACKUP_BUCKET}/${BACKUP_DIR}/${BACKUP_FILENAME}"

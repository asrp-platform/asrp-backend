#!/bin/bash
# No silent fail
set -euo pipefail

BACKUP_DATE=$(date -u +"%Y-%m-%d_%H-%M-%S_UTC"

BACKUP_BUCKET="backups"
BACKUP_DIR="database_backups"
BACKUP_FILENAME="${DB_NAME}_${BACKUP_DATE}.dump"

# s3 searches credentials as AWS_
export AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$S3_SECRET_KEY"
export AWS_DEFAULT_REGION="${S3_REGION:-auto}"

pg_dump \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -Fc \
  -Z 6 \
  --no-owner \
  -- no-acl \
| aws s3 cp - "s3://${BACKUP_BUCKET}/${BACKUP_DIR}/${BACKUP_FILENAME}" --endpoint-url "$S3_ENDPOINT"

exho "Backup uploaded: s3://${BACKUP_BUCKET}/${BACKUP_DIR}/${BACKUP_FILENAME}"

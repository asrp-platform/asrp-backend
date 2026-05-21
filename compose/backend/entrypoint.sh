#!/bin/sh

set -e

export DB_HOST="${DB_HOST:-asrp_database}"

alembic upgrade head
uvicorn app.main:app --host 0.0.0.0

#!/bin/sh

export DB_HOST="${DB_HOST:-asrp_database}"

poetry run alembic upgrade head
poetry run uvicorn app.main:app --host 0.0.0.0

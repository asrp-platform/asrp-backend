#!/bin/sh

mkdir -p media
mkdir -p media/news_uploads
mkdir -p media/directors_board_uploads
mkdir -p media/bylaws

export DB_HOST="${DB_HOST:-asrp_database}"

poetry run alembic upgrade head
poetry run uvicorn app.main:app --host 0.0.0.0

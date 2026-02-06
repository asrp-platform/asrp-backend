#!/bin/sh

mkdir media
mkdir media/news_uploads
mkdir media/directors_board_uploads
mkdir media/bylaws

export DB_HOST=asrp_database

poetry run alembic upgrade head
poetry run uvicorn app.main:app --host 0.0.0.0

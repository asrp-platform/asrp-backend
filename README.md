# ASRP Backend

## Backend Setup Guide

This guide explains how to run the **PostgreSQL database** and the **FastAPI backend** for the ASRP project in two common scenarios:

1. Running **Database + Backend via Docker**
2. Running **only the Database via Docker** and starting the backend locally from an IDE

### Setup development environment using Docker

## Environment Configuration

Create a `.env` file in the project root.

#### Start and build containers

```shell
docker compose -f ./local.yml --build -d
```

Database migrations are applied automatically

For deployment the `DB_HOST` environment variable should match the database service name specified in `local.yml`.
For local development set `DB_HOST` to `localhost`.


### Setup development environment using IDE

#### Start and build database container

```shell
docker compose up -d asrp_database
```

#### Install dependencies

```shell
poetry install
```

#### Apply database migrations

```shell
alembic upgrade head
```

#### Run the app

```shell
uvicorn app.main:app --reload
```

## Naming

### Branch naming

The following branch types are used according to the GitFlow development workflow:

1. `feature/*` - for features
2. `release/*`
3. `hotfix/*`
4. `bugfix/*`

### Commits naming

We use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) to name our commits using the following special words:

- docs: (msg) — for documentation changes
- refactor: (msg) — for code refactoring without changing behavior
- test: (msg) — for adding or updating tests
- chore: (msg) — for maintenance tasks


## Main services

### App

Root URL of api must start with `api/` prefix. For example:

```
http://localhost:8000/api/users/1
```

### Database


### Media files storage

the storage is accessible via `MEDIA_PATH_NAME/file_name`. For example:

```
http://localhost:8000/api/media/photo.jpeg
```

### Tests

Run tests

```shell
pytest -v tests
```

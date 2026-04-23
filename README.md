# ASRP Backend




## Backend Setup Guide

This guide explains how to run the **PostgreSQL database** and the **FastAPI backend** for the ASRP project in two common scenarios:

1. Running **Database + Backend via Docker**
2. Running **only the Database via Docker** and starting the backend locally from an IDE






## Setup development environment using Docker


### Environment Configuration

Create a `.env` file in the project root using `.env-template` configuration file.

Necessary envs:

- `DB_HOST=localhost` - localhost if starting backend via IDE, container name is using Docker,
- `DB_PORT=5432`
- `DB_PASSWORD=asrp_test`
- `DB_USER=asrp_test`
- `DB_NAME=asrp_test`


- `DEV_MODE=true`

- `SECRET_KEY`
- `FERNET_KEY`
- `ALGORITHM=HS256`

- `S3_ACCESS_KEY=minio_admin`
- `S3_SECRET_KEY=minio_admin`
- `S3_BUCKET=uploads`
- `S3_REGION=us-east-1`

- `S3_ENDPOINT=http://localhost:9000`
- `S3_PUBLIC_URL=http://localhost:9000`

`SECRET_KEY` and `FERNET_KEY` must be generated manually

#### DB_HOST

When running backend inside Docker:
DB_HOST=asrp_database

When running backend locally from IDE:
DB_HOST=localhost

#### DEV_MODE

DEV_MODE enables:
- mocked email sending
- relaxed security checks
- development logging


#### Fernet Key generation

```python
from cryptography.fernet import Fernet

print(Fernet.generate_key().decode())
```

#### Secret Key generation

```python
import secrets

print(secrets.token_urlsafe(64))
```

#### Stripe Api Key

Ask team lead to get restricted stripe api key


#### Stripe Webhook Secret

STRIPE_WEBHOOK_SECRET can be retrieved from the stripe-cli docker container. Check the container logs after it started


### Start and build containers

```shell
docker compose -f ./local.yml up --build -d
```

Database migrations are applied automatically using `alembic upgrade head` command in *compose/backend/entrypoint.sh*

For deployment the `DB_HOST` environment variable should match the database service name specified in `local.yml`.
For local development set `DB_HOST` to `localhost`.


### Setup development environment using IDE

#### Start and build database container (DEV)

```shell
docker compose -f local.yml up -d asrp_database minio
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

All feature, bugfix, and release branches must be created from the develop branch.

The following branch types are used according to the GitFlow development workflow:

1. `feature/*`
2. `release/*`
3. `hotfix/*`
4. `bugfix/*`
5. `refactor/*`

### Pull requests naming

1. `Feature: *`
2. `Release: *`
3. `Hotfix: *`
4. `Bugfix: *`
5. `Refactor: *`

### Commits naming

We use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) to name our commits using the following special words:

- feat: (msg) - for new features
- fix: (msg) - for bug fixing
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


### File storage

We use MinIO as a file storage. Minio web interface is accessible via

```
http://localhost:9001/login
```

### Stripe CLI

If backend is running as a docker-container command in `local.yml` need must be:

```yml
listen --forward-to http://asrp_backend:8000/api/payments/stripe/webhook --events checkout.session.completed,checkout.session.async_payment_succeeded,checkout.session.async_payment_failed,payment_intent.succeeded,payment_intent.payment_failed
```

If backend runs on a host mush be set as a `host.docker.internal`:

```yml
listen --forward-to http://host.docker.internal:8000/api/payments/stripe/webhook --events checkout.session.completed,checkout.session.async_payment_succeeded,checkout.session.async_payment_failed,payment_intent.succeeded,payment_intent.payment_failed
```


### Tests

All tests are run using a dedicated test database.

```shell
pytest -v tests
```


## Troubleshooting


### Get all existing permissions script

```sql
INSERT INTO users_permissions (permission_id, user_id)
SELECT p.id, 1
FROM permissions p
WHERE NOT EXISTS (
    SELECT 1
    FROM users_permissions up
    WHERE up.permission_id = p.id
      AND up.user_id = 1
);
```

### Update nginx config in container

```shell
docker exec nginx_server service nginx restart
```

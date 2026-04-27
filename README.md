# ASRP Backend

## Local development setup guide

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


- `STRIPE_API_KEY` - call team lead to get if needed
- `STRIPE_WEBHOOK_SECRET` - can be gotten from stripe-cli


- `FRONTEND_DOMAIN_HTTP=http://localhost:3000`
- `FRONTEND_DOMAIN=http://localhost:3000`

`SECRET_KEY` and `FERNET_KEY` must be generated manually

#### DB_HOST

When running backend locally using IDE:
`DB_HOST=localhost`

When running backend inside Docker (deployment case):
`DB_HOST=asrp_database`

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

`STRIPE_WEBHOOK_SECRET` can be retrieved from the stripe-cli docker container. Check the container logs after it started


### Start and build containers

```shell
docker compose -f ./local.yml up --build -d
```

### Install dependencies

```shell
poetry install
```

### Install pre-commit

```bash
pre-commit install
```

### Apply database migrations

```shell
alembic upgrade head
```

### Run the app

```shell
uvicorn app.main:app --reload
```

### Run tests

All tests are run using a dedicated test database.

```shell
pytest -v tests
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


## Services

### App

FastAPI application is defined in `app/main.py`.

When the app is started locally with Uvicorn, it is available at:

```shell
http://localhost:8000
```

API routes are mounted under the `/api` prefix. For example:

```
http://localhost:8000/api/users/1
```

Healthcheck endpoint:

```shell
http://localhost:8000/healthcheck
```

### Database

PostgreSQL is used as the main database.


### File storage

MinIO is used as S3-compatible file storage.

S3 API endpoint:

```shell
http://localhost:9000
```

MinIO web console:

```shell
http://localhost:9001/login
```

Credentials are taken from `S3_ACCESS_KEY` and `S3_SECRET_KEY`.

The default bucket is configured by `S3_BUCKET` or `S3_DEFAULT_BUCKET`.


### Stripe CLI

Stripe CLI is used to forward Stripe webhook events to the backend.

In `local.yml`, the service command points to:

```shell
http://localhost:8000/api/payments/stripe/webhook
```

The service listens for these events:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `checkout.session.async_payment_failed`
- `payment_intent.succeeded`
- `payment_intent.payment_failed`

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
docker exec nginx service nginx restart
```

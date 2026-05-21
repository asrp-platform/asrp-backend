FROM python:3.12.3-slim

ENV POETRY_VERSION=2.1.3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PATH="/root/.local/bin:$PATH"

RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION && \
    apt-get remove -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root --no-interaction --no-ansi

COPY alembic.ini ./
COPY ./compose/backend/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh

COPY ./alembic ./alembic
COPY ./app ./app

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

EXPOSE 8000

FROM python:3.12.3-slim


RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get remove -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root

COPY ./compose/backend/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

COPY ./alembic ./
COPY alembic.ini ./

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

EXPOSE 8000

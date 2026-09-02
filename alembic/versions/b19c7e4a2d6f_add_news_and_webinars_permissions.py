"""add news and webinars permissions

Revision ID: b19c7e4a2d6f
Revises: 74a15cde3921
Create Date: 2026-08-16 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from app.core.config import DEV_MODE


revision: str = "b19c7e4a2d6f"
down_revision: Union[str, None] = "74a15cde3921"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = (
    ("webinars.create", "Create webinars"),
    ("webinars.view", "View webinars"),
    ("webinars.update", "Update webinars"),
    ("webinars.delete", "Delete webinars"),
    ("news.create", "Create news"),
    ("news.view", "View news"),
    ("news.update", "Update news"),
    ("news.delete", "Delete news"),
)
PERMISSION_ACTIONS_SQL = ", ".join(f"'{action}'" for action, _ in PERMISSIONS)


def upgrade() -> None:
    metadata = sa.MetaData()
    permissions_table = sa.Table("permissions", metadata, autoload_with=op.get_bind())
    op.bulk_insert(
        permissions_table,
        [{"action": action, "name": name} for action, name in PERMISSIONS],
    )

    if DEV_MODE:
        op.execute(
            "INSERT INTO users_permissions (permission_id, user_id) "
            "SELECT id, 1 FROM permissions "
            f"WHERE action IN ({PERMISSION_ACTIONS_SQL})"
        )


def downgrade() -> None:
    op.execute(
        "DELETE FROM users_permissions WHERE permission_id IN "
        f"(SELECT id FROM permissions WHERE action IN ({PERMISSION_ACTIONS_SQL}))"
    )
    op.execute(f"DELETE FROM permissions WHERE action IN ({PERMISSION_ACTIONS_SQL})")

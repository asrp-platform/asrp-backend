"""add_user_management_permissions

Revision ID: c0560a10ef3c
Revises: 31057bd009bb
Create Date: 2026-06-03 14:53:01.756052

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from app.core.config import DEV_MODE


# revision identifiers, used by Alembic.
revision: str = "c0560a10ef3c"
down_revision: Union[str, None] = "31057bd009bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    metadata = sa.MetaData()
    bind = op.get_bind()
    permissions_table = sa.Table("permissions", metadata, autoload_with=bind)

    new_permissions = [
        {"action": "users.create", "name": "Create users"},
        {"action": "users.view", "name": "View users"},
        {"action": "users.delete", "name": "Remove users"},
        {"action": "users.update", "name": "Update users"},
    ]
    op.bulk_insert(permissions_table, new_permissions)

    if DEV_MODE:
        op.execute(
            "INSERT INTO users_permissions (permission_id, user_id) "
            "SELECT id, 1 FROM permissions WHERE action IN "
            "('users.create', 'users.view', 'users.delete', 'users.update')"
        )


def downgrade() -> None:
    op.execute(
        "DELETE FROM users_permissions WHERE permission_id IN "
        "(SELECT id FROM permissions WHERE action IN "
        "('users.create', 'users.view', 'users.delete', 'users.update'))"
    )
    op.execute("DELETE FROM permissions WHERE action IN ('users.create', 'users.view', 'users.delete', 'users.update')")

"""add payments permissions

Revision ID: 8f7b5e4c2d3a
Revises: 5dd727aa08c6
Create Date: 2026-05-27 12:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from app.core.config import DEV_MODE


# revision identifiers, used by Alembic.
revision: str = "8f7b5e4c2d3a"
down_revision: Union[str, None] = "5dd727aa08c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    metadata = sa.MetaData()
    bind = op.get_bind()

    permissions_table = sa.Table(
        "permissions",
        metadata,
        autoload_with=bind,
    )

    op.bulk_insert(
        permissions_table,
        [
            {"action": "payments.create", "name": "Create payments"},
            {"action": "payments.view", "name": "View payments"},
            {"action": "payments.update", "name": "Update payments"},
            {"action": "payments.delete", "name": "Delete payments"},
        ],
    )

    if DEV_MODE:
        op.execute(
            """
            INSERT INTO users_permissions (permission_id, user_id)
            SELECT id, 1 FROM permissions
            WHERE action IN ('payments.create', 'payments.view', 'payments.update', 'payments.delete')
            """
        )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM users_permissions
        WHERE permission_id IN (
            SELECT id FROM permissions
            WHERE action IN ('payments.create', 'payments.view', 'payments.update', 'payments.delete')
        )
        """
    )

    op.execute(
        """
        DELETE FROM permissions
        WHERE action IN ('payments.create', 'payments.view', 'payments.update', 'payments.delete')
        """
    )

"""username_change permissions

Revision ID: ec60ae60d61d
Revises: 78a6c82b5bd6
Create Date: 2026-02-20 10:36:04.176734

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ec60ae60d61d'
down_revision: Union[str, None] = '78a6c82b5bd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    permissions_table = sa.table(
        "permissions", sa.column("action", sa.String), sa.column("name", sa.String), sa.column("_deleted", sa.Boolean)
    )

    op.bulk_insert(
        permissions_table,
        [
            {"action": "username_change.view", "name": "View username changes"},
            {"action": "username_change.update", "name": "Approve/reject username changes"},
        ],
    )


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            DELETE FROM permissions WHERE action IN (
            'username_change.view',
            'username_change.update'
            )
        """)
    )

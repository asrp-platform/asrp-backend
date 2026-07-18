"""membership types permissions

Revision ID: 6de1b0ef7687
Revises: 94c7026014d3
Create Date: 2026-07-15 00:10:25.249449

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from app.core.config import DEV_MODE


# revision identifiers, used by Alembic.
revision: str = "6de1b0ef7687"
down_revision: Union[str, None] = "94c7026014d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    metadata = sa.MetaData()
    bind = op.get_bind()
    permissions_table = sa.Table("permissions", metadata, autoload_with=bind)

    new_permissions = [
        {"action": "membership_types.create", "name": "Create membership types"},
        {"action": "membership_types.view", "name": "View membership types"},
        {"action": "membership_types.delete", "name": "Delete membership types"},
        {"action": "membership_types.update", "name": "Update membership types"},
    ]
    op.bulk_insert(permissions_table, new_permissions)

    if DEV_MODE:
        op.execute(
            "INSERT INTO users_permissions (permission_id, user_id) "
            "SELECT id, 1 FROM permissions WHERE action IN "
            "('membership_types.create', 'membership_types.view', "
            "'membership_types.delete', 'membership_types.update')"
        )


def downgrade() -> None:
    op.execute(
        "DELETE FROM users_permissions WHERE permission_id IN "
        "(SELECT id FROM permissions WHERE action IN "
        "('membership_types.create', 'membership_types.view', "
        "'membership_types.delete', 'membership_types.update'))"
    )
    op.execute(
        "DELETE FROM permissions WHERE action IN "
        "('membership_types.create', 'membership_types.view', "
        "'membership_types.delete', 'membership_types.update')"
    )

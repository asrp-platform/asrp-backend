"""add user deleted_at

Revision ID: 7e4b920a6d13
Revises: bccf1fc16e0d
Create Date: 2026-10-30

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "7e4b920a6d13"
down_revision: Union[str, None] = "bccf1fc16e0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "deleted_at")

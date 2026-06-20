"""update user registration confirmation fields

Revision ID: 873e793efaf6
Revises: 5dd727aa08c6
Create Date: 2026-05-25 00:09:06.873270

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "873e793efaf6"
down_revision: Union[str, None] = "5dd727aa08c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "email_confirmed")
    op.drop_column("users", "institution")
    op.drop_column("users", "role")


def downgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(), nullable=True))
    op.add_column("users", sa.Column("institution", sa.String(), nullable=True))
    op.add_column("users", sa.Column("email_confirmed", sa.Boolean(), server_default=sa.text("false"), nullable=False))

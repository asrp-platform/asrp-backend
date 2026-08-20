"""add public webinar registration link

Revision ID: d5e8f31a4b72
Revises: af7689e668d1
Create Date: 2026-08-20

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "d5e8f31a4b72"
down_revision: Union[str, None] = "af7689e668d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("webinars", sa.Column("registration_link", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("webinars", "registration_link")

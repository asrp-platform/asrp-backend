"""remove webinar registration link

Revision ID: a91f0b62d183
Revises: 189b514682e6
Create Date: 2026-08-09

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "a91f0b62d183"
down_revision: Union[str, None] = "189b514682e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("webinars", "registration_link")


def downgrade() -> None:
    op.add_column("webinars", sa.Column("registration_link", sa.Text(), nullable=True))

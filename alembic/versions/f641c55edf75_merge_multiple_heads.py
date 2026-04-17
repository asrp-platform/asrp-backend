"""Merge multiple heads

Revision ID: f641c55edf75
Revises: 32b2d70c1d06, d6de1a40ad1f
Create Date: 2026-04-17 23:25:11.209268

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "f641c55edf75"
down_revision: Union[str, None] = ("32b2d70c1d06", "d6de1a40ad1f")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

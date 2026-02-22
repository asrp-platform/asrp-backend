"""Merge two heads into one

Revision ID: 0f7e4c431a00
Revises: 43b61ebfc7c6, f40e24e4429d
Create Date: 2026-02-22 19:54:49.835451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f7e4c431a00'
down_revision: Union[str, None] = ('43b61ebfc7c6', 'f40e24e4429d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

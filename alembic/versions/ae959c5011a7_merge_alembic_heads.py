"""merge alembic heads

Revision ID: ae959c5011a7
Revises: 50ef4536f557, e25423541c91
Create Date: 2026-04-11 21:02:26.442491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae959c5011a7'
down_revision: Union[str, None] = ('50ef4536f557', 'e25423541c91')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

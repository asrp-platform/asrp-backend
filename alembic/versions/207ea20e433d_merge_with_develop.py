"""merge with develop

Revision ID: 207ea20e433d
Revises: 43b61ebfc7c6, f9780a34a084
Create Date: 2026-02-23 14:50:04.870422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '207ea20e433d'
down_revision: Union[str, None] = ('43b61ebfc7c6', 'f9780a34a084')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

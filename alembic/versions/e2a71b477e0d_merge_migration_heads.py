"""merge migration heads

Revision ID: e2a71b477e0d
Revises: 2d66df0d3c74, 873e793efaf6
Create Date: 2026-05-29 21:33:44.798409

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "e2a71b477e0d"
down_revision: Union[str, None] = ("2d66df0d3c74", "873e793efaf6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

"""merge heads

Revision ID: 32b2d70c1d06
Revises: ae959c5011a7, 11412859c713
Create Date: 2026-04-12 13:55:31.476211

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "32b2d70c1d06"
down_revision: Union[str, None] = ("ae959c5011a7", "11412859c713")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

"""merge alembic heads

Revision ID: 43b61ebfc7c6
Revises: 78a6c82b5bd6, b9dc4ec67c04
Create Date: 2026-02-19 16:18:38.598198

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "43b61ebfc7c6"
down_revision: Union[str, None] = ("78a6c82b5bd6", "b9dc4ec67c04")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

"""merge migration heads

Revision ID: c85804cc0c22
Revises: 8f7b5e4c2d3a, e2a71b477e0d
Create Date: 2026-05-30 14:22:13.142300

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "c85804cc0c22"
down_revision: Union[str, None] = ("8f7b5e4c2d3a", "e2a71b477e0d")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

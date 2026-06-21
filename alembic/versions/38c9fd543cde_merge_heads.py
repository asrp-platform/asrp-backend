"""merge heads

Revision ID: 38c9fd543cde
Revises: c0560a10ef3c, 15b185145d89
Create Date: 2026-06-21 17:13:16.231604

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "38c9fd543cde"
down_revision: Union[str, None] = ("c0560a10ef3c", "15b185145d89")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

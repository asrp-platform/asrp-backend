"""merge_user_profile_with_legal_docs

Revision ID: 008
Revises: 007_add_user_profile_fields, 007
Create Date: 2026-02-07 18:14:48.346566

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = ('007_add_user_profile_fields', '007')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

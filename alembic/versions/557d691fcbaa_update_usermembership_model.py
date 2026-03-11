"""update UserMembership model

Revision ID: 557d691fcbaa
Revises: b99d31e2536a
Create Date: 2026-03-03 12:39:20.590156

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '557d691fcbaa'
down_revision: Union[str, None] = 'b99d31e2536a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users_memberships', sa.Column('primary_affiliation', sa.String(), nullable=False))
    op.add_column('users_memberships', sa.Column('job_title', sa.String(), nullable=False))
    op.add_column('users_memberships', sa.Column('practice_setting', sa.String(), nullable=False))
    op.add_column('users_memberships', sa.Column('subspecialty', sa.String(), nullable=False))
    op.add_column('users_memberships', sa.Column('is_trained_in_us', sa.Boolean(), nullable=False))
    op.drop_column('users_memberships', 'has_access')


def downgrade() -> None:
    op.add_column('users_memberships', sa.Column('has_access', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.drop_column('users_memberships', 'is_trained_in_us')
    op.drop_column('users_memberships', 'subspecialty')
    op.drop_column('users_memberships', 'practice_setting')
    op.drop_column('users_memberships', 'job_title')
    op.drop_column('users_memberships', 'primary_affiliation')

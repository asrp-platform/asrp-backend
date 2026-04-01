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
    op.add_column('users_memberships', sa.Column('primary_affiliation', sa.String(), nullable=True))
    op.add_column('users_memberships', sa.Column('job_title', sa.String(), nullable=True))
    op.add_column('users_memberships', sa.Column('practice_setting', sa.String(), nullable=True))
    op.add_column('users_memberships', sa.Column('subspecialty', sa.String(), nullable=True))
    op.add_column('users_memberships', sa.Column('is_trained_in_us', sa.Boolean(), nullable=True))

    op.execute(
        """
        UPDATE users_memberships
        SET
            primary_affiliation = '',
            job_title = '',
            practice_setting = '',
            subspecialty = '',
            is_trained_in_us = FALSE
        WHERE
            primary_affiliation IS NULL
            OR job_title IS NULL
            OR practice_setting IS NULL
            OR subspecialty IS NULL
            OR is_trained_in_us IS NULL
        """
    )

    op.alter_column("users_memberships", "primary_affiliation", nullable=False)
    op.alter_column("users_memberships", "job_title", nullable=False)
    op.alter_column("users_memberships", "practice_setting", nullable=False)
    op.alter_column("users_memberships", "subspecialty", nullable=False)
    op.alter_column("users_memberships", "is_trained_in_us", nullable=False)


def downgrade() -> None:
    op.drop_column('users_memberships', 'is_trained_in_us')
    op.drop_column('users_memberships', 'subspecialty')
    op.drop_column('users_memberships', 'practice_setting')
    op.drop_column('users_memberships', 'job_title')
    op.drop_column('users_memberships', 'primary_affiliation')

"""FeedbackAdditionalInfo model

Revision ID: b99d31e2536a
Revises: 207ea20e433d
Create Date: 2026-03-03 12:31:53.148988

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b99d31e2536a'
down_revision: Union[str, None] = '207ea20e433d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('feedback_additional_infos',
    sa.Column('hear_about_asrp', sa.String(), nullable=False),
    sa.Column('tg_username', sa.String(), nullable=True),
    sa.Column('interest_description', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_feedback_additional_infos_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_feedback_additional_infos')),
    sa.UniqueConstraint('user_id', name=op.f('uq_feedback_additional_infos_user_id'))
    )


def downgrade() -> None:
    op.drop_table('feedback_additional_infos')

"""add_email_templates_and_permissions

Revision ID: 97201fa620b1
Revises: 6de1b0ef7687
Create Date: 2026-07-17 09:31:01.530560

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from app.core.config import DEV_MODE


revision: str = '97201fa620b1'
down_revision: Union[str, None] = '6de1b0ef7687'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('email_templates',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('subject', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('editor_state', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('html', sa.String(), nullable=False),
    sa.Column('_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_email_templates'))
    )

    metadata = sa.MetaData()
    bind = op.get_bind()
    permissions_table = sa.Table("permissions", metadata, autoload_with=bind)

    new_permissions = [
        {"action": "email_templates.create", "name": "Create email templates"},
        {"action": "email_templates.view", "name": "View email templates"},
        {"action": "email_templates.delete", "name": "Remove email templates"},
        {"action": "email_templates.update", "name": "Update email templates"},
    ]
    op.bulk_insert(permissions_table, new_permissions)

    if DEV_MODE:
        op.execute(
            "INSERT INTO users_permissions (permission_id, user_id) "
            "SELECT id, 1 FROM permissions WHERE action IN "
            "('email_templates.create', 'email_templates.view', 'email_templates.delete', 'email_templates.update')"
        )


def downgrade() -> None:
    op.drop_table('email_templates')

    op.execute(
        "DELETE FROM users_permissions WHERE permission_id IN "
        "(SELECT id FROM permissions WHERE action IN "
        "('email_templates.create', 'email_templates.view', 'email_templates.delete', 'email_templates.update'))"
    )
    op.execute("DELETE FROM permissions WHERE action IN ('email_templates.create', 'email_templates.view', 'email_templates.delete', 'email_templates.update')")

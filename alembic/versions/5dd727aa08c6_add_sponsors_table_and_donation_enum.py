"""Add sponsors table and donation enum

Revision ID: 5dd727aa08c6
Revises: 6e29a6badfb9
Create Date: 2026-05-14 17:35:25.549479

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5dd727aa08c6"
down_revision: Union[str, None] = "6e29a6badfb9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENUM_NAME = "contact_message_type_enum"
NEW_VALUE = "DONATION_SPONSORSHIP"

OLD_VALUES = (
    "CONTACT",
    "GET_INVOLVED",
    "GET_INVOLVED_COMMITTEES",
)

NEW_VALUES = (
    *OLD_VALUES,
    NEW_VALUE,
)


def upgrade() -> None:
    op.create_table(
        "sponsors",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("short_name", sa.String(), nullable=True),
        sa.Column("logo_key", sa.String(), nullable=True),
        sa.Column("link", sa.String(), nullable=False),
        sa.Column("_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sponsors")),
    )

    op.execute(
        f"""
        ALTER TYPE {ENUM_NAME}
        ADD VALUE '{NEW_VALUE}'
        """
    )


def downgrade() -> None:
    op.drop_table("sponsors")

    #
    # Проверяем что enum value не используется
    #
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM contact_messages
                WHERE type = '{NEW_VALUE}'
            ) THEN
                RAISE EXCEPTION
                    'Cannot downgrade: enum value {NEW_VALUE} is still used';
            END IF;
        END$$;
        """
    )

    #
    # Создаём новый enum без DONATION_SPONSORSHIP
    #
    old_values_sql = ", ".join(f"'{v}'" for v in OLD_VALUES)

    op.execute(
        f"""
        CREATE TYPE {ENUM_NAME}_old AS ENUM (
            {old_values_sql}
        )
        """
    )

    #
    # Переводим колонку на новый enum
    #
    op.execute(
        f"""
        ALTER TABLE contact_messages
        ALTER COLUMN type
        TYPE {ENUM_NAME}_old
        USING type::text::{ENUM_NAME}_old
        """
    )

    #
    # Удаляем старый enum
    #
    op.execute(f"DROP TYPE {ENUM_NAME}")

    #
    # Переименовываем новый
    #
    op.execute(
        f"""
        ALTER TYPE {ENUM_NAME}_old
        RENAME TO {ENUM_NAME}
        """
    )

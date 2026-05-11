"""positive amount constarint

Revision ID: 6e29a6badfb9
Revises: 04c788d04f52
Create Date: 2026-05-08 17:34:52.942517

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6e29a6badfb9"
down_revision: Union[str, None] = "04c788d04f52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        op.f("ck_payments_amount_positive"),
        "payments",
        "amount > 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_payments_amount_positive"),
        "payments",
        type_="check",
    )

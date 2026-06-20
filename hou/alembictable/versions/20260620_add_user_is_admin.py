"""add user is_admin

Revision ID: 20260620_add_user_is_admin
Revises: b0d7846a28fc
Create Date: 2026-06-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260620_add_user_is_admin"
down_revision: Union[str, None] = "b0d7846a28fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("is_admin", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("user", "is_admin")

"""add user created_time

Revision ID: 20260624_add_user_created_time
Revises: 20260624_add_payment_order_flow
Create Date: 2026-06-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260624_add_user_created_time"
down_revision: Union[str, None] = "20260624_add_payment_order_flow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _column_exists("user", "created_time"):
        op.add_column(
            "user",
            sa.Column(
                "created_time",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )
    if not _index_exists("user", "ix_user_created_time"):
        op.create_index("ix_user_created_time", "user", ["created_time"])


def downgrade() -> None:
    op.drop_index("ix_user_created_time", table_name="user")
    op.drop_column("user", "created_time")

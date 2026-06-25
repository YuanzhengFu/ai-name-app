"""add login record

Revision ID: 20260625_add_login_record
Revises: 20260625_add_preference_template_default
Create Date: 2026-06-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260625_add_login_record"
down_revision: Union[str, None] = "20260625_add_preference_template_default"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if _table_exists("login_record"):
        return
    op.create_table(
        "login_record",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("success", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("failure_reason", sa.String(length=100), nullable=True),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_login_record_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_login_record")),
    )
    op.create_index(op.f("ix_login_record_user_id"), "login_record", ["user_id"], unique=False)
    op.create_index(op.f("ix_login_record_email"), "login_record", ["email"], unique=False)
    op.create_index(op.f("ix_login_record_created_time"), "login_record", ["created_time"], unique=False)


def downgrade() -> None:
    if _table_exists("login_record"):
        op.drop_table("login_record")

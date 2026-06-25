"""add name history

Revision ID: 20260623_add_name_history
Revises: 20260620_add_user_is_admin
Create Date: 2026-06-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260623_add_name_history"
down_revision: Union[str, None] = "20260620_add_user_is_admin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "name_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("reference", sa.Text(), nullable=False),
        sa.Column("moral", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(length=255), server_default="", nullable=False),
        sa.Column("domain_status", sa.String(length=100), server_default="", nullable=False),
        sa.Column("surname", sa.String(length=100), server_default="", nullable=False),
        sa.Column("gender", sa.String(length=20), server_default="", nullable=False),
        sa.Column("length", sa.String(length=20), server_default="", nullable=False),
        sa.Column("other", sa.Text(), nullable=True),
        sa.Column("exclude", sa.Text(), nullable=False),
        sa.Column("is_favorite", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_name_history_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_name_history")),
    )
    op.create_index("ix_name_history_user_created", "name_history", ["user_id", "created_time"])
    op.create_index("ix_name_history_user_favorite", "name_history", ["user_id", "is_favorite"])
    op.create_index(op.f("ix_name_history_thread_id"), "name_history", ["thread_id"])
    op.create_index(op.f("ix_name_history_category"), "name_history", ["category"])


def downgrade() -> None:
    op.drop_index(op.f("ix_name_history_category"), table_name="name_history")
    op.drop_index(op.f("ix_name_history_thread_id"), table_name="name_history")
    op.drop_index("ix_name_history_user_favorite", table_name="name_history")
    op.drop_index("ix_name_history_user_created", table_name="name_history")
    op.drop_table("name_history")

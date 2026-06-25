"""add knowledge task is_active

Revision ID: 20260624_add_knowledge_task_is_active
Revises: 20260623_add_knowledge_task
Create Date: 2026-06-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260624_add_knowledge_task_is_active"
down_revision: Union[str, None] = "20260623_add_knowledge_task"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _column_exists("knowledge_task", "is_active"):
        op.add_column(
            "knowledge_task",
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        )
    if not _index_exists("knowledge_task", "ix_knowledge_task_user_active"):
        op.create_index("ix_knowledge_task_user_active", "knowledge_task", ["user_id", "is_active"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_task_user_active", table_name="knowledge_task")
    op.drop_column("knowledge_task", "is_active")

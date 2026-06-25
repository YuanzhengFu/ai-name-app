"""add knowledge task parse metadata

Revision ID: 20260625_add_knowledge_task_parse_metadata
Revises: 20260625_add_preference_template_default
Create Date: 2026-06-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260625_add_knowledge_task_parse_metadata"
down_revision: Union[str, None] = "20260625_add_preference_template_default"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _column_exists("knowledge_task", "chunk_count"):
        op.add_column(
            "knowledge_task",
            sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
        )
    if not _column_exists("knowledge_task", "parse_log"):
        op.add_column("knowledge_task", sa.Column("parse_log", sa.Text(), nullable=True))
    if not _index_exists("knowledge_task", "ix_knowledge_task_project_status"):
        op.create_index("ix_knowledge_task_project_status", "knowledge_task", ["project_id", "status"])


def downgrade() -> None:
    if _index_exists("knowledge_task", "ix_knowledge_task_project_status"):
        op.drop_index("ix_knowledge_task_project_status", table_name="knowledge_task")
    if _column_exists("knowledge_task", "parse_log"):
        op.drop_column("knowledge_task", "parse_log")
    if _column_exists("knowledge_task", "chunk_count"):
        op.drop_column("knowledge_task", "chunk_count")

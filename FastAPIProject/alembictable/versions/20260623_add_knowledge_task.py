"""add knowledge task

Revision ID: 20260623_add_knowledge_task
Revises: 20260623_add_name_history
Create Date: 2026-06-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260623_add_knowledge_task"
down_revision: Union[str, None] = "20260623_add_name_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_task",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="queued", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_time", sa.DateTime(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_knowledge_task_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_task")),
    )
    op.create_index(op.f("ix_knowledge_task_user_id"), "knowledge_task", ["user_id"])
    op.create_index(op.f("ix_knowledge_task_status"), "knowledge_task", ["status"])
    op.create_index("ix_knowledge_task_created", "knowledge_task", ["created_time"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_task_created", table_name="knowledge_task")
    op.drop_index(op.f("ix_knowledge_task_status"), table_name="knowledge_task")
    op.drop_index(op.f("ix_knowledge_task_user_id"), table_name="knowledge_task")
    op.drop_table("knowledge_task")

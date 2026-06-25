"""add naming projects

Revision ID: 20260624_add_naming_projects
Revises: 20260624_add_user_created_time
Create Date: 2026-06-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260624_add_naming_projects"
down_revision: Union[str, None] = "20260624_add_user_created_time"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _foreign_key_exists(table_name: str, fk_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return fk_name in {fk["name"] for fk in inspector.get_foreign_keys(table_name)}


def upgrade() -> None:
    if not _table_exists("naming_project"):
        op.create_table(
            "naming_project",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("category", sa.String(length=20), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
            sa.Column("created_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_naming_project_user_id_user")),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_naming_project")),
        )
    if not _index_exists("naming_project", op.f("ix_naming_project_user_id")):
        op.create_index(op.f("ix_naming_project_user_id"), "naming_project", ["user_id"])
    if not _index_exists("naming_project", op.f("ix_naming_project_category")):
        op.create_index(op.f("ix_naming_project_category"), "naming_project", ["category"])
    if not _index_exists("naming_project", op.f("ix_naming_project_status")):
        op.create_index(op.f("ix_naming_project_status"), "naming_project", ["status"])

    if not _column_exists("name_history", "project_id"):
        op.add_column("name_history", sa.Column("project_id", sa.Integer(), nullable=True))
    if not _index_exists("name_history", op.f("ix_name_history_project_id")):
        op.create_index(op.f("ix_name_history_project_id"), "name_history", ["project_id"])
    if not _foreign_key_exists("name_history", op.f("fk_name_history_project_id_naming_project")):
        op.create_foreign_key(
            op.f("fk_name_history_project_id_naming_project"),
            "name_history",
            "naming_project",
            ["project_id"],
            ["id"],
        )

    if not _column_exists("knowledge_task", "project_id"):
        op.add_column("knowledge_task", sa.Column("project_id", sa.Integer(), nullable=True))
    if not _index_exists("knowledge_task", op.f("ix_knowledge_task_project_id")):
        op.create_index(op.f("ix_knowledge_task_project_id"), "knowledge_task", ["project_id"])
    if not _foreign_key_exists("knowledge_task", op.f("fk_knowledge_task_project_id_naming_project")):
        op.create_foreign_key(
            op.f("fk_knowledge_task_project_id_naming_project"),
            "knowledge_task",
            "naming_project",
            ["project_id"],
            ["id"],
        )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_knowledge_task_project_id_naming_project"), "knowledge_task", type_="foreignkey")
    op.drop_index(op.f("ix_knowledge_task_project_id"), table_name="knowledge_task")
    op.drop_column("knowledge_task", "project_id")

    op.drop_constraint(op.f("fk_name_history_project_id_naming_project"), "name_history", type_="foreignkey")
    op.drop_index(op.f("ix_name_history_project_id"), table_name="name_history")
    op.drop_column("name_history", "project_id")

    op.drop_index(op.f("ix_naming_project_status"), table_name="naming_project")
    op.drop_index(op.f("ix_naming_project_category"), table_name="naming_project")
    op.drop_index(op.f("ix_naming_project_user_id"), table_name="naming_project")
    op.drop_table("naming_project")

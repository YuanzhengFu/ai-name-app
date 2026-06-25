"""add user generation quota

Revision ID: 20260624_add_user_generation_quota
Revises: 20260624_add_name_scores, 20260624_add_knowledge_task_is_active
Create Date: 2026-06-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260624_add_user_generation_quota"
down_revision: Union[str, tuple[str, str], None] = (
    "20260624_add_name_scores",
    "20260624_add_knowledge_task_is_active",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    table_existed = _table_exists("user_generation_quota")
    if not table_existed:
        op.create_table(
            "user_generation_quota",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("total_quota", sa.Integer(), server_default="10", nullable=False),
            sa.Column("used_quota", sa.Integer(), server_default="0", nullable=False),
            sa.Column("created_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_user_generation_quota_user_id_user")),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_user_generation_quota")),
            sa.UniqueConstraint("user_id", name=op.f("uq_user_generation_quota_user_id")),
        )
    if not _index_exists("user_generation_quota", op.f("ix_user_generation_quota_user_id")):
        op.create_index(op.f("ix_user_generation_quota_user_id"), "user_generation_quota", ["user_id"])

    user_table = sa.table("user", sa.column("id", sa.Integer))
    quota_table = sa.table(
        "user_generation_quota",
        sa.column("user_id", sa.Integer),
        sa.column("total_quota", sa.Integer),
        sa.column("used_quota", sa.Integer),
    )
    if not table_existed:
        op.execute(
            quota_table.insert().from_select(
                ["user_id", "total_quota", "used_quota"],
                sa.select(user_table.c.id, sa.literal(10), sa.literal(0)),
            )
        )
    else:
        op.execute(
            sa.text(
                "INSERT IGNORE INTO user_generation_quota (user_id, total_quota, used_quota) "
                "SELECT id, 10, 0 FROM user"
            )
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_generation_quota_user_id"), table_name="user_generation_quota")
    op.drop_table("user_generation_quota")

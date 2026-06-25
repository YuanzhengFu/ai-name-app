"""add preference templates

Revision ID: 20260624_add_preference_templates
Revises: 20260624_add_naming_projects
Create Date: 2026-06-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260624_add_preference_templates"
down_revision: Union[str, None] = "20260624_add_naming_projects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _table_exists("naming_preference_template"):
        op.create_table(
            "naming_preference_template",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("category", sa.String(length=20), nullable=False),
            sa.Column("preferences", sa.JSON(), nullable=False),
            sa.Column("created_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_naming_preference_template_user_id_user")),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_naming_preference_template")),
        )
    if not _index_exists("naming_preference_template", op.f("ix_naming_preference_template_user_id")):
        op.create_index(op.f("ix_naming_preference_template_user_id"), "naming_preference_template", ["user_id"])
    if not _index_exists("naming_preference_template", op.f("ix_naming_preference_template_category")):
        op.create_index(op.f("ix_naming_preference_template_category"), "naming_preference_template", ["category"])


def downgrade() -> None:
    op.drop_index(op.f("ix_naming_preference_template_category"), table_name="naming_preference_template")
    op.drop_index(op.f("ix_naming_preference_template_user_id"), table_name="naming_preference_template")
    op.drop_table("naming_preference_template")

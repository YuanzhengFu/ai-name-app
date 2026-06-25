"""add preference template default flag

Revision ID: 20260625_add_preference_template_default
Revises: 20260624_add_preference_templates
Create Date: 2026-06-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260625_add_preference_template_default"
down_revision: Union[str, None] = "20260624_add_preference_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _column_exists("naming_preference_template", "is_default"):
        op.add_column(
            "naming_preference_template",
            sa.Column("is_default", sa.Boolean(), server_default=sa.false(), nullable=False),
        )


def downgrade() -> None:
    if _column_exists("naming_preference_template", "is_default"):
        op.drop_column("naming_preference_template", "is_default")

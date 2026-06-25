"""add company name enrichment fields

Revision ID: 20260625_add_company_name_enrichment
Revises: 20260625_add_preference_template_default
Create Date: 2026-06-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260625_add_company_name_enrichment"
down_revision: Union[str, None] = "20260625_add_preference_template_default"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    columns = [
        ("domain_checks", sa.Column("domain_checks", sa.Text(), nullable=True)),
        ("brand_warning", sa.Column("brand_warning", sa.Text(), nullable=True)),
        ("pinyin", sa.Column("pinyin", sa.String(length=255), server_default="", nullable=False)),
        ("english_name", sa.Column("english_name", sa.String(length=255), server_default="", nullable=False)),
        ("abbreviation", sa.Column("abbreviation", sa.String(length=50), server_default="", nullable=False)),
    ]
    for column_name, column in columns:
        if not _column_exists("name_history", column_name):
            op.add_column("name_history", column)
    if _column_exists("name_history", "domain_checks"):
        op.execute(sa.text("UPDATE name_history SET domain_checks = '[]' WHERE domain_checks IS NULL"))
        op.alter_column("name_history", "domain_checks", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    for column_name in ("abbreviation", "english_name", "pinyin", "brand_warning", "domain_checks"):
        if _column_exists("name_history", column_name):
            op.drop_column("name_history", column_name)

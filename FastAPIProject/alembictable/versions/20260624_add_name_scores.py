"""add name scores

Revision ID: 20260624_add_name_scores
Revises: 20260623_add_knowledge_task
Create Date: 2026-06-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260624_add_name_scores"
down_revision: Union[str, None] = "20260623_add_knowledge_task"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    columns = [
        ("score_total", sa.Column("score_total", sa.Integer(), server_default="0", nullable=False)),
        ("rhythm_score", sa.Column("rhythm_score", sa.Integer(), server_default="0", nullable=False)),
        ("meaning_score", sa.Column("meaning_score", sa.Integer(), server_default="0", nullable=False)),
        ("spread_score", sa.Column("spread_score", sa.Integer(), server_default="0", nullable=False)),
        ("domain_score", sa.Column("domain_score", sa.Integer(), server_default="0", nullable=False)),
        ("score_explanation", sa.Column("score_explanation", sa.Text(), nullable=True)),
    ]
    for column_name, column in columns:
        if not _column_exists("name_history", column_name):
            op.add_column("name_history", column)


def downgrade() -> None:
    op.drop_column("name_history", "score_explanation")
    op.drop_column("name_history", "domain_score")
    op.drop_column("name_history", "spread_score")
    op.drop_column("name_history", "meaning_score")
    op.drop_column("name_history", "rhythm_score")
    op.drop_column("name_history", "score_total")

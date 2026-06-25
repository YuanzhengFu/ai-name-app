"""merge 20260625 migration heads

Revision ID: 20260626_merge_20260625_heads
Revises: 20260625_add_company_name_enrichment, 20260625_add_knowledge_task_parse_metadata, 20260625_add_login_record
Create Date: 2026-06-26

"""
from typing import Sequence, Union


revision: str = "20260626_merge_20260625_heads"
down_revision: Union[str, tuple[str, ...], None] = (
    "20260625_add_company_name_enrichment",
    "20260625_add_knowledge_task_parse_metadata",
    "20260625_add_login_record",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

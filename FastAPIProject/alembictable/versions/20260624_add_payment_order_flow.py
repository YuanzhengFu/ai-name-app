"""add payment order flow

Revision ID: 20260624_add_payment_order_flow
Revises: 20260624_add_membership_system
Create Date: 2026-06-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260624_add_payment_order_flow"
down_revision: Union[str, None] = "20260624_add_membership_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    columns = [
        ("provider", sa.Column("provider", sa.String(length=20), server_default="mock", nullable=False)),
        ("provider_trade_no", sa.Column("provider_trade_no", sa.String(length=100), server_default="", nullable=False)),
        ("payment_payload", sa.Column("payment_payload", sa.Text(), nullable=True)),
        ("failure_reason", sa.Column("failure_reason", sa.Text(), nullable=True)),
        ("refunded_time", sa.Column("refunded_time", sa.DateTime(), nullable=True)),
        ("updated_time", sa.Column("updated_time", sa.DateTime(), server_default=sa.func.now(), nullable=False)),
    ]
    for column_name, column in columns:
        if not _column_exists("recharge_order", column_name):
            op.add_column("recharge_order", column)
    op.execute(sa.text("UPDATE recharge_order SET payment_payload = '' WHERE payment_payload IS NULL"))
    op.execute(sa.text("UPDATE recharge_order SET failure_reason = '' WHERE failure_reason IS NULL"))
    op.alter_column("recharge_order", "status", server_default="pending", existing_type=sa.String(length=20))
    if not _index_exists("recharge_order", op.f("ix_recharge_order_provider")):
        op.create_index(op.f("ix_recharge_order_provider"), "recharge_order", ["provider"])
    if not _index_exists("recharge_order", op.f("ix_recharge_order_provider_trade_no")):
        op.create_index(op.f("ix_recharge_order_provider_trade_no"), "recharge_order", ["provider_trade_no"])


def downgrade() -> None:
    op.drop_index(op.f("ix_recharge_order_provider_trade_no"), table_name="recharge_order")
    op.drop_index(op.f("ix_recharge_order_provider"), table_name="recharge_order")
    op.alter_column("recharge_order", "status", server_default="paid", existing_type=sa.String(length=20))
    op.drop_column("recharge_order", "updated_time")
    op.drop_column("recharge_order", "refunded_time")
    op.drop_column("recharge_order", "failure_reason")
    op.drop_column("recharge_order", "payment_payload")
    op.drop_column("recharge_order", "provider_trade_no")
    op.drop_column("recharge_order", "provider")

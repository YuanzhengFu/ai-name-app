"""add membership system

Revision ID: 20260624_add_membership_system
Revises: 20260624_add_user_generation_quota
Create Date: 2026-06-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260624_add_membership_system"
down_revision: Union[str, None] = "20260624_add_user_generation_quota"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "membership_plan",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price_cents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("credits", sa.Integer(), server_default="0", nullable=False),
        sa.Column("validity_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_membership_plan")),
    )
    op.create_index(op.f("ix_membership_plan_is_active"), "membership_plan", ["is_active"])

    op.create_table(
        "user_membership",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_name", sa.String(length=100), server_default="免费版", nullable=False),
        sa.Column("credit_balance", sa.Integer(), server_default="10", nullable=False),
        sa.Column("total_recharged", sa.Integer(), server_default="10", nullable=False),
        sa.Column("total_consumed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_user_membership_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_membership")),
        sa.UniqueConstraint("user_id", name=op.f("uq_user_membership_user_id")),
    )
    op.create_index(op.f("ix_user_membership_user_id"), "user_membership", ["user_id"])

    op.create_table(
        "credit_transaction",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("change_amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=50), server_default="", nullable=False),
        sa.Column("remark", sa.Text(), nullable=False),
        sa.Column("operator_id", sa.Integer(), nullable=True),
        sa.Column("created_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_credit_transaction_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_credit_transaction")),
    )
    op.create_index(op.f("ix_credit_transaction_user_id"), "credit_transaction", ["user_id"])
    op.create_index(op.f("ix_credit_transaction_transaction_type"), "credit_transaction", ["transaction_type"])
    op.create_index(op.f("ix_credit_transaction_created_time"), "credit_transaction", ["created_time"])

    op.create_table(
        "recharge_order",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("plan_name", sa.String(length=100), nullable=False),
        sa.Column("amount_cents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("credits", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="paid", nullable=False),
        sa.Column("paid_time", sa.DateTime(), nullable=True),
        sa.Column("created_time", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["membership_plan.id"], name=op.f("fk_recharge_order_plan_id_membership_plan")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_recharge_order_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recharge_order")),
    )
    op.create_index(op.f("ix_recharge_order_user_id"), "recharge_order", ["user_id"])
    op.create_index(op.f("ix_recharge_order_plan_id"), "recharge_order", ["plan_id"])
    op.create_index(op.f("ix_recharge_order_status"), "recharge_order", ["status"])

    plan_table = sa.table(
        "membership_plan",
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("price_cents", sa.Integer),
        sa.column("credits", sa.Integer),
        sa.column("validity_days", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        plan_table,
        [
            {
                "name": "体验包",
                "description": "适合轻量体验，含 30 次 AI 起名额度",
                "price_cents": 990,
                "credits": 30,
                "validity_days": 0,
                "is_active": True,
                "sort_order": 10,
            },
            {
                "name": "标准包",
                "description": "适合个人和小团队，含 120 次 AI 起名额度",
                "price_cents": 2990,
                "credits": 120,
                "validity_days": 0,
                "is_active": True,
                "sort_order": 20,
            },
            {
                "name": "专业包",
                "description": "适合品牌顾问和高频使用，含 500 次 AI 起名额度",
                "price_cents": 9900,
                "credits": 500,
                "validity_days": 0,
                "is_active": True,
                "sort_order": 30,
            },
        ],
    )

    user_table = sa.table("user", sa.column("id", sa.Integer))
    quota_table = sa.table(
        "user_generation_quota",
        sa.column("user_id", sa.Integer),
        sa.column("total_quota", sa.Integer),
        sa.column("used_quota", sa.Integer),
    )
    membership_table = sa.table(
        "user_membership",
        sa.column("user_id", sa.Integer),
        sa.column("plan_name", sa.String),
        sa.column("credit_balance", sa.Integer),
        sa.column("total_recharged", sa.Integer),
        sa.column("total_consumed", sa.Integer),
    )
    select_existing_quota = sa.select(
        user_table.c.id,
        sa.literal("免费版"),
        sa.func.greatest(sa.func.coalesce(quota_table.c.total_quota, 10) - sa.func.coalesce(quota_table.c.used_quota, 0), 0),
        sa.func.coalesce(quota_table.c.total_quota, 10),
        sa.func.coalesce(quota_table.c.used_quota, 0),
    ).select_from(user_table.outerjoin(quota_table, user_table.c.id == quota_table.c.user_id))
    op.execute(
        membership_table.insert().from_select(
            ["user_id", "plan_name", "credit_balance", "total_recharged", "total_consumed"],
            select_existing_quota,
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_recharge_order_status"), table_name="recharge_order")
    op.drop_index(op.f("ix_recharge_order_plan_id"), table_name="recharge_order")
    op.drop_index(op.f("ix_recharge_order_user_id"), table_name="recharge_order")
    op.drop_table("recharge_order")
    op.drop_index(op.f("ix_credit_transaction_created_time"), table_name="credit_transaction")
    op.drop_index(op.f("ix_credit_transaction_transaction_type"), table_name="credit_transaction")
    op.drop_index(op.f("ix_credit_transaction_user_id"), table_name="credit_transaction")
    op.drop_table("credit_transaction")
    op.drop_index(op.f("ix_user_membership_user_id"), table_name="user_membership")
    op.drop_table("user_membership")
    op.drop_index(op.f("ix_membership_plan_is_active"), table_name="membership_plan")
    op.drop_table("membership_plan")

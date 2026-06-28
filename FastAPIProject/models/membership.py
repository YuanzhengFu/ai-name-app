from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class MembershipPlan(Base):
    __tablename__ = "membership_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", server_default="", nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    credits: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    validity_days: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class UserMembership(Base):
    __tablename__ = "user_membership"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True, nullable=False)
    plan_name: Mapped[str] = mapped_column(String(100), default="免费版", server_default="免费版", nullable=False)
    credit_balance: Mapped[int] = mapped_column(Integer, default=10, server_default="10", nullable=False)
    total_recharged: Mapped[int] = mapped_column(Integer, default=10, server_default="10", nullable=False)
    total_consumed: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


class CreditTransaction(Base):
    __tablename__ = "credit_transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)
    change_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="", server_default="", nullable=False)
    remark: Mapped[str] = mapped_column(Text, default="", server_default="", nullable=False)
    operator_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, index=True)


class RechargeOrder(Base):
    __tablename__ = "recharge_order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("membership_plan.id"), index=True, nullable=False)
    plan_name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    credits: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(20), default="alipay", server_default="alipay", index=True, nullable=False)
    provider_trade_no: Mapped[str] = mapped_column(String(100), default="", server_default="", index=True, nullable=False)
    payment_payload: Mapped[str] = mapped_column(Text, default="", server_default="", nullable=False)
    failure_reason: Mapped[str] = mapped_column(Text, default="", server_default="", nullable=False)
    paid_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    refunded_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

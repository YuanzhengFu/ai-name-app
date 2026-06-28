from datetime import datetime
from typing import Annotated
from typing import Literal

from pydantic import BaseModel, Field


class MembershipPlanBase(BaseModel):
    name: Annotated[str, Field(..., min_length=1, max_length=100)]
    description: str = ""
    price_cents: Annotated[int, Field(ge=0)] = 0
    credits: Annotated[int, Field(ge=1)] = 1
    validity_days: Annotated[int, Field(ge=0)] = 0
    is_active: bool = True
    sort_order: int = 0


class MembershipPlanCreateIn(MembershipPlanBase):
    pass


class MembershipPlanUpdateIn(BaseModel):
    name: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    description: str | None = None
    price_cents: Annotated[int | None, Field(ge=0)] = None
    credits: Annotated[int | None, Field(ge=1)] = None
    validity_days: Annotated[int | None, Field(ge=0)] = None
    is_active: bool | None = None
    sort_order: int | None = None


class MembershipPlanOut(MembershipPlanBase):
    id: int
    created_time: datetime
    updated_time: datetime

    model_config = {"from_attributes": True}


class MembershipAccountOut(BaseModel):
    user_id: int
    plan_name: str
    credit_balance: int
    total_recharged: int
    total_consumed: int
    expires_at: datetime | None = None
    updated_time: datetime


class RechargeIn(BaseModel):
    plan_id: int
    pay_scene: Literal["page", "wap"] = "page"


class RechargeOrderOut(BaseModel):
    id: int
    user_id: int
    plan_id: int
    plan_name: str
    amount_cents: int
    credits: int
    status: str
    provider: str
    provider_trade_no: str = ""
    payment_payload: str = ""
    failure_reason: str = ""
    paid_time: datetime | None = None
    refunded_time: datetime | None = None
    created_time: datetime
    updated_time: datetime

    model_config = {"from_attributes": True}


class PaymentRefundIn(BaseModel):
    reason: Annotated[str, Field(min_length=1, max_length=500)] = "Payment refund"


class CreditTransactionOut(BaseModel):
    id: int
    user_id: int
    change_amount: int
    balance_after: int
    transaction_type: str
    source: str
    remark: str
    operator_id: int | None = None
    created_time: datetime

    model_config = {"from_attributes": True}


class CreditTransactionListOut(BaseModel):
    items: list[CreditTransactionOut]
    total: int
    limit: Annotated[int, Field(ge=1, le=100)]
    offset: Annotated[int, Field(ge=0)]


class AdminCreditAdjustIn(BaseModel):
    amount: Annotated[int, Field(..., ge=-100000, le=100000)]
    reason: Annotated[str, Field(..., min_length=1, max_length=500)]


class AdminCreditAdjustOut(BaseModel):
    account: MembershipAccountOut
    transaction: CreditTransactionOut

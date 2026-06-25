from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.auth import AuthHandler
from core.membership_service import (
    ORDER_STATUS_FAILED,
    ORDER_STATUS_PAID,
    ORDER_STATUS_PROCESSING,
    ORDER_STATUS_REFUNDED,
    MembershipService,
    account_to_dict,
)
from dependencies import get_session
from models.membership import RechargeOrder
from schemas.membership_schemas import (
    CreditTransactionListOut,
    MembershipAccountOut,
    MembershipPlanOut,
    PaymentNotifyIn,
    RechargeIn,
    RechargeOrderOut,
)

auth_handler = AuthHandler()
router = APIRouter(prefix="/membership", tags=["membership"])


@router.get("/plans", response_model=list[MembershipPlanOut])
async def list_plans(session: AsyncSession = Depends(get_session)):
    return await MembershipService(session).list_active_plans()


@router.get("/me", response_model=MembershipAccountOut)
async def my_membership(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    account = await MembershipService(session).get_or_create_account(user_id)
    return account_to_dict(account)


@router.post("/recharge", response_model=RechargeOrderOut)
async def recharge(
    data: RechargeIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    order = await MembershipService(session).recharge(user_id, data.plan_id, data.provider)
    return order


@router.get("/orders/{order_id}", response_model=RechargeOrderOut)
async def get_recharge_order(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await MembershipService(session).get_order(user_id, order_id)


@router.post("/orders/{order_id}/processing", response_model=RechargeOrderOut)
async def mark_recharge_order_processing(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    service = MembershipService(session)
    await service.get_order(user_id, order_id)
    return await service.mark_order_processing(order_id)


@router.post("/orders/{order_id}/mock-pay", response_model=RechargeOrderOut)
async def mock_pay_recharge_order(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    service = MembershipService(session)
    order = await service.get_order(user_id, order_id)
    if order.provider != "mock":
        raise HTTPException(status_code=400, detail="Only mock payment orders can use this endpoint")
    order, _ = await service.mark_order_paid(order_id, provider_trade_no=f"mock-{order_id}")
    return order


@router.post("/payment/notify/{provider}")
async def payment_notify(
    provider: str,
    data: PaymentNotifyIn,
    session: AsyncSession = Depends(get_session),
):
    try:
        order_id = int(data.out_trade_no)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid out_trade_no") from exc

    service = MembershipService(session)
    order = await session.get(RechargeOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.provider != provider:
        raise HTTPException(status_code=400, detail="Payment provider does not match order")

    normalized_status = data.status.lower()
    if normalized_status in {ORDER_STATUS_PAID, "success", "trade_success", "trade_finished"}:
        order, _ = await service.mark_order_paid(order_id, data.trade_no)
    elif normalized_status in {ORDER_STATUS_PROCESSING, "paying", "userpaying"}:
        order = await service.mark_order_processing(order_id)
    elif normalized_status in {ORDER_STATUS_REFUNDED, "refund", "refunded"}:
        order, _ = await service.refund_order(order_id, data.message or f"{provider} refund")
    else:
        order = await service.mark_order_failed(order_id, data.message or f"{provider} payment failed")
    return {"ok": True, "order_id": order.id, "status": order.status}


@router.get("/transactions", response_model=CreditTransactionListOut)
async def my_transactions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    items, total = await MembershipService(session).list_transactions(user_id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}

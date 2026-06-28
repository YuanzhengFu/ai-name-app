from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.responses import PlainTextResponse
from starlette.status import HTTP_410_GONE

from core.alipay_service import ALIPAY_STATUS_FAILED, ALIPAY_STATUS_PROCESSING, ALIPAY_STATUS_SUCCESS, AlipayService
from core.auth import AuthHandler
from core.membership_service import (
    MembershipService,
    account_to_dict,
)
from dependencies import get_session
from models.membership import RechargeOrder
from schemas.membership_schemas import (
    CreditTransactionListOut,
    MembershipAccountOut,
    MembershipPlanOut,
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
    order = await MembershipService(session).recharge(user_id, data.plan_id, data.pay_scene)
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
    raise HTTPException(status_code=HTTP_410_GONE, detail="Mock payment has been disabled; use Alipay sandbox")


@router.post("/orders/{order_id}/alipay-query", response_model=RechargeOrderOut)
async def query_alipay_recharge_order(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    service = MembershipService(session)
    order = await service.get_order(user_id, order_id)
    if order.provider != "alipay":
        raise HTTPException(status_code=400, detail="Only alipay orders can be queried")
    return await service.sync_alipay_query(order_id)


@router.post("/payment/notify/{provider}")
async def payment_notify(
    provider: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    if provider != "alipay":
        raise HTTPException(status_code=400, detail="Only alipay sandbox payment is supported")

    form = await request.form()
    data = {key: str(value) for key, value in form.items()}
    if not AlipayService().verify_notify(data):
        return PlainTextResponse("failure", status_code=400)

    try:
        order_id = int(data.get("out_trade_no", ""))
    except ValueError:
        return PlainTextResponse("failure", status_code=400)

    service = MembershipService(session)
    order = await session.get(RechargeOrder, order_id)
    if not order:
        return PlainTextResponse("failure", status_code=404)
    if order.provider != provider:
        return PlainTextResponse("failure", status_code=400)

    trade_status = data.get("trade_status", "").upper()
    if trade_status in ALIPAY_STATUS_SUCCESS:
        order, _ = await service.mark_order_paid(order_id, data.get("trade_no", ""))
    elif trade_status in ALIPAY_STATUS_PROCESSING:
        order = await service.mark_order_processing(order_id)
    elif trade_status in ALIPAY_STATUS_FAILED:
        order = await service.mark_order_failed(order_id, trade_status)
    else:
        return PlainTextResponse("failure", status_code=400)
    return PlainTextResponse("success")


@router.get("/transactions", response_model=CreditTransactionListOut)
async def my_transactions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    items, total = await MembershipService(session).list_transactions(user_id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}

import json
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_402_PAYMENT_REQUIRED, HTTP_404_NOT_FOUND

from models.membership import CreditTransaction, MembershipPlan, RechargeOrder, UserMembership


DEFAULT_FREE_CREDITS = 10

ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_PROCESSING = "processing"
ORDER_STATUS_PAID = "paid"
ORDER_STATUS_FAILED = "failed"
ORDER_STATUS_REFUNDED = "refunded"

PAYMENT_PROVIDER_MOCK = "mock"
PAYMENT_PROVIDER_WECHAT = "wechat"
PAYMENT_PROVIDER_ALIPAY = "alipay"
PAYMENT_PROVIDERS = {PAYMENT_PROVIDER_MOCK, PAYMENT_PROVIDER_WECHAT, PAYMENT_PROVIDER_ALIPAY}


def account_to_dict(account: UserMembership) -> dict:
    return {
        "user_id": account.user_id,
        "plan_name": account.plan_name,
        "credit_balance": account.credit_balance,
        "total_recharged": account.total_recharged,
        "total_consumed": account.total_consumed,
        "expires_at": account.expires_at,
        "updated_time": account.updated_time,
    }


class MembershipService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_account(self, user_id: int) -> UserMembership:
        account = await self.session.scalar(select(UserMembership).where(UserMembership.user_id == user_id))
        if account:
            return account

        account = UserMembership(
            user_id=user_id,
            credit_balance=DEFAULT_FREE_CREDITS,
            total_recharged=DEFAULT_FREE_CREDITS,
        )
        self.session.add(account)
        await self.session.flush()
        self.session.add(
            CreditTransaction(
                user_id=user_id,
                change_amount=DEFAULT_FREE_CREDITS,
                balance_after=DEFAULT_FREE_CREDITS,
                transaction_type="grant",
                source="system",
                remark="New user free credits",
            )
        )
        await self.session.commit()
        await self.session.refresh(account)
        return account

    async def _get_locked_account(self, user_id: int) -> UserMembership:
        await self.get_or_create_account(user_id)
        account = await self.session.scalar(
            select(UserMembership)
            .where(UserMembership.user_id == user_id)
            .with_for_update()
        )
        if not account:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Credit account not found")
        return account

    async def list_active_plans(self) -> list[MembershipPlan]:
        result = await self.session.execute(
            select(MembershipPlan)
            .where(MembershipPlan.is_active.is_(True))
            .order_by(MembershipPlan.sort_order.asc(), MembershipPlan.price_cents.asc(), MembershipPlan.id.asc())
        )
        return list(result.scalars().all())

    async def list_plans(self, include_inactive: bool = False) -> list[MembershipPlan]:
        statement = select(MembershipPlan)
        if not include_inactive:
            statement = statement.where(MembershipPlan.is_active.is_(True))
        result = await self.session.execute(
            statement.order_by(MembershipPlan.sort_order.asc(), MembershipPlan.id.asc())
        )
        return list(result.scalars().all())

    async def create_plan(self, data) -> MembershipPlan:
        plan = MembershipPlan(**data.model_dump())
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def update_plan(self, plan_id: int, data) -> MembershipPlan:
        plan = await self.session.get(MembershipPlan, plan_id)
        if not plan:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Membership plan not found")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(plan, key, value)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def recharge(self, user_id: int, plan_id: int, provider: str = PAYMENT_PROVIDER_MOCK) -> RechargeOrder:
        provider = provider.lower()
        if provider not in PAYMENT_PROVIDERS:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Unsupported payment provider")

        plan = await self.session.get(MembershipPlan, plan_id)
        if not plan or not plan.is_active:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Membership plan not found or inactive")

        await self.get_or_create_account(user_id)
        order = RechargeOrder(
            user_id=user_id,
            plan_id=plan.id,
            plan_name=plan.name,
            amount_cents=plan.price_cents,
            credits=plan.credits,
            status=ORDER_STATUS_PENDING,
            provider=provider,
        )
        self.session.add(order)
        await self.session.flush()
        order.payment_payload = self._build_payment_payload(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    def _build_payment_payload(self, order: RechargeOrder) -> str:
        payload = {
            "provider": order.provider,
            "out_trade_no": str(order.id),
            "amount_cents": order.amount_cents,
            "description": f"Membership plan: {order.plan_name}",
        }
        if order.provider == PAYMENT_PROVIDER_MOCK:
            payload["checkout_url"] = f"mock://pay/orders/{order.id}"
        elif order.provider == PAYMENT_PROVIDER_WECHAT:
            payload["trade_type"] = "JSAPI"
            payload["notify_url"] = "/membership/payment/notify/wechat"
        elif order.provider == PAYMENT_PROVIDER_ALIPAY:
            payload["product_code"] = "FAST_INSTANT_TRADE_PAY"
            payload["notify_url"] = "/membership/payment/notify/alipay"
        return json.dumps(payload, ensure_ascii=False)

    async def get_order(self, user_id: int, order_id: int) -> RechargeOrder:
        order = await self.session.get(RechargeOrder, order_id)
        if not order or order.user_id != user_id:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Order not found")
        return order

    async def mark_order_processing(self, order_id: int) -> RechargeOrder:
        order = await self.session.get(RechargeOrder, order_id, with_for_update=True)
        if not order:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Order not found")
        if order.status == ORDER_STATUS_PENDING:
            order.status = ORDER_STATUS_PROCESSING
            await self.session.commit()
            await self.session.refresh(order)
        return order

    async def mark_order_paid(self, order_id: int, provider_trade_no: str = "") -> tuple[RechargeOrder, UserMembership | None]:
        order = await self.session.get(RechargeOrder, order_id, with_for_update=True)
        if not order:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Order not found")
        if order.status == ORDER_STATUS_PAID:
            account = await self.session.scalar(select(UserMembership).where(UserMembership.user_id == order.user_id))
            return order, account
        if order.status in {ORDER_STATUS_FAILED, ORDER_STATUS_REFUNDED}:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Order cannot be paid in current status")

        order.status = ORDER_STATUS_PAID
        order.paid_time = datetime.now()
        order.provider_trade_no = provider_trade_no or order.provider_trade_no
        account = await self._credit_paid_order(order)
        await self.session.commit()
        await self.session.refresh(order)
        await self.session.refresh(account)
        return order, account

    async def _credit_paid_order(self, order: RechargeOrder) -> UserMembership:
        account = await self._get_locked_account(order.user_id)
        account.plan_name = order.plan_name
        account.credit_balance += order.credits
        account.total_recharged += order.credits

        plan = await self.session.get(MembershipPlan, order.plan_id)
        if plan and plan.validity_days > 0:
            base_time = account.expires_at if account.expires_at and account.expires_at > datetime.now() else datetime.now()
            account.expires_at = base_time + timedelta(days=plan.validity_days)

        self.session.add(
            CreditTransaction(
                user_id=order.user_id,
                change_amount=order.credits,
                balance_after=account.credit_balance,
                transaction_type="recharge",
                source=order.provider,
                remark=f"Order #{order.id}: {order.plan_name}",
            )
        )
        return account

    async def mark_order_failed(self, order_id: int, reason: str = "") -> RechargeOrder:
        order = await self.session.get(RechargeOrder, order_id, with_for_update=True)
        if not order:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Order not found")
        if order.status == ORDER_STATUS_FAILED:
            return order
        if order.status not in {ORDER_STATUS_PENDING, ORDER_STATUS_PROCESSING}:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Order cannot be failed in current status")
        order.status = ORDER_STATUS_FAILED
        order.failure_reason = reason
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def refund_order(self, order_id: int, reason: str = "Payment refund") -> tuple[RechargeOrder, UserMembership]:
        order = await self.session.get(RechargeOrder, order_id, with_for_update=True)
        if not order:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Order not found")
        if order.status == ORDER_STATUS_REFUNDED:
            account = await self.session.scalar(select(UserMembership).where(UserMembership.user_id == order.user_id))
            if not account:
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Credit account not found")
            return order, account
        if order.status != ORDER_STATUS_PAID:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Only paid orders can be refunded")

        account = await self._get_locked_account(order.user_id)
        if account.credit_balance < order.credits:
            await self.session.rollback()
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Insufficient credit balance to refund order")

        account.credit_balance -= order.credits
        account.total_recharged = max(0, account.total_recharged - order.credits)
        order.status = ORDER_STATUS_REFUNDED
        order.refunded_time = datetime.now()
        self.session.add(
            CreditTransaction(
                user_id=order.user_id,
                change_amount=-order.credits,
                balance_after=account.credit_balance,
                transaction_type="payment_refund",
                source=order.provider,
                remark=f"Refund order #{order.id}: {reason}",
            )
        )
        await self.session.commit()
        await self.session.refresh(order)
        await self.session.refresh(account)
        return order, account

    async def consume(self, user_id: int, amount: int = 1, remark: str = "AI name generation") -> CreditTransaction:
        if amount <= 0:
            raise ValueError("amount must be positive")

        account = await self._get_locked_account(user_id)
        if account.credit_balance < amount:
            await self.session.rollback()
            raise HTTPException(status_code=HTTP_402_PAYMENT_REQUIRED, detail="Insufficient credits, please recharge first")

        account.credit_balance -= amount
        account.total_consumed += amount
        transaction = CreditTransaction(
            user_id=user_id,
            change_amount=-amount,
            balance_after=account.credit_balance,
            transaction_type="consume",
            source="names",
            remark=remark,
        )
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def refund(self, user_id: int, amount: int = 1, remark: str = "Generation failed refund") -> None:
        if amount <= 0:
            return

        account = await self._get_locked_account(user_id)
        account.credit_balance += amount
        account.total_consumed = max(0, account.total_consumed - amount)
        self.session.add(
            CreditTransaction(
                user_id=user_id,
                change_amount=amount,
                balance_after=account.credit_balance,
                transaction_type="refund",
                source="names",
                remark=remark,
            )
        )
        await self.session.commit()

    async def admin_adjust(self, user_id: int, amount: int, reason: str, operator_id: int) -> tuple[UserMembership, CreditTransaction]:
        if amount == 0:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Credit adjustment cannot be 0")

        account = await self._get_locked_account(user_id)
        if account.credit_balance + amount < 0:
            await self.session.rollback()
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Credit balance cannot be negative")

        account.credit_balance += amount
        if amount > 0:
            account.total_recharged += amount

        transaction = CreditTransaction(
            user_id=user_id,
            change_amount=amount,
            balance_after=account.credit_balance,
            transaction_type="admin_adjust",
            source="admin",
            remark=reason,
            operator_id=operator_id,
        )
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(account)
        await self.session.refresh(transaction)
        return account, transaction

    async def list_transactions(self, user_id: int, limit: int = 20, offset: int = 0) -> tuple[list[CreditTransaction], int]:
        total = await self.session.scalar(
            select(func.count()).select_from(CreditTransaction).where(CreditTransaction.user_id == user_id)
        )
        result = await self.session.execute(
            select(CreditTransaction)
            .where(CreditTransaction.user_id == user_id)
            .order_by(CreditTransaction.created_time.desc(), CreditTransaction.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), int(total or 0)

import json

from sqlalchemy import func, select

from core.membership_service import DEFAULT_FREE_CREDITS
from core.email_rate_limit import COOLDOWN_PREFIX, IP_LIMIT_PREFIX
from models.membership import CreditTransaction, RechargeOrder, UserMembership
from models.security import LoginRecord
from tests.conftest import auth_headers, create_plan, create_user


async def test_register_login_and_default_membership(client, fake_redis, session_maker):
    code_response = await client.get("/auth/code", params={"email": "new@example.com"})
    assert code_response.status_code == 200
    code = fake_redis.values["new@example.com"]

    register_response = await client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "username": "new-user",
            "password": "password123",
            "confirm_password": "password123",
            "code": code,
        },
    )
    assert register_response.status_code == 200

    login_response = await client.post(
        "/auth/login",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["token"]

    async with session_maker() as session:
        account = await session.scalar(select(UserMembership).where(UserMembership.user_id == 1))
        assert account is not None
        assert account.credit_balance == DEFAULT_FREE_CREDITS


async def test_reset_password_with_email_code(client, fake_redis, session_maker):
    await create_user(session_maker, email="reset@example.com")
    fake_redis.values["reset@example.com"] = "1234"

    reset_response = await client.post(
        "/auth/password/reset",
        json={
            "email": "reset@example.com",
            "code": "1234",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
    )
    assert reset_response.status_code == 200
    assert "reset@example.com" not in fake_redis.values

    old_login_response = await client.post(
        "/auth/login",
        json={"email": "reset@example.com", "password": "password123"},
    )
    assert old_login_response.status_code == 400

    new_login_response = await client.post(
        "/auth/login",
        json={"email": "reset@example.com", "password": "newpassword123"},
    )
    assert new_login_response.status_code == 200


async def test_change_email_with_password_and_code(client, fake_redis, session_maker):
    user = await create_user(session_maker, email="olduser@example.com")
    fake_redis.values["new-email@example.com"] = "2468"

    change_response = await client.post(
        "/users/me/email",
        json={
            "new_email": "new-email@example.com",
            "code": "2468",
            "password": "password123",
        },
        headers=auth_headers(user.id),
    )
    assert change_response.status_code == 200
    assert change_response.json()["email"] == "new-email@example.com"
    assert "new-email@example.com" not in fake_redis.values

    login_response = await client.post(
        "/auth/login",
        json={"email": "new-email@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200


async def test_login_records_are_created_and_listed(client, session_maker):
    user = await create_user(session_maker, email="record@example.com")

    failed_response = await client.post(
        "/auth/login",
        json={"email": "record@example.com", "password": "wrong-password"},
        headers={"user-agent": "pytest-agent"},
    )
    assert failed_response.status_code == 400

    success_response = await client.post(
        "/auth/login",
        json={"email": "record@example.com", "password": "password123"},
        headers={"user-agent": "pytest-agent"},
    )
    assert success_response.status_code == 200

    records_response = await client.get("/users/me/login-records", headers=auth_headers(user.id))
    assert records_response.status_code == 200
    records = records_response.json()
    assert len(records) == 2
    assert {item["success"] for item in records} == {True, False}
    assert any(item["failure_reason"] == "invalid_password" for item in records)

    async with session_maker() as session:
        count = await session.scalar(
            select(func.count()).select_from(LoginRecord).where(LoginRecord.user_id == user.id)
        )
        assert count == 2


async def test_admin_can_reset_user_password(client, session_maker):
    user = await create_user(session_maker, email="target@example.com")
    admin = await create_user(session_maker, email="admin-reset@example.com", is_admin=True)

    reset_response = await client.post(
        f"/admin/users/{user.id}/password",
        json={"new_password": "adminset123", "confirm_password": "adminset123"},
        headers=auth_headers(admin.id),
    )
    assert reset_response.status_code == 200

    login_response = await client.post(
        "/auth/login",
        json={"email": "target@example.com", "password": "adminset123"},
    )
    assert login_response.status_code == 200


async def test_email_code_rate_limits_same_email(client, fake_redis):
    first_response = await client.get("/auth/code", params={"email": "limit@example.com"})
    assert first_response.status_code == 200

    second_response = await client.get("/auth/code", params={"email": "limit@example.com"})
    assert second_response.status_code == 429
    assert "验证码发送太频繁" in second_response.json()["detail"]


async def test_email_code_rate_limits_same_ip(client, fake_redis):
    for index in range(20):
        fake_redis.values.pop(f"{COOLDOWN_PREFIX}:ip{index}@example.com", None)
        response = await client.get("/auth/code", params={"email": f"ip{index}@example.com"})
        assert response.status_code == 200

    fake_redis.values.pop(f"{COOLDOWN_PREFIX}:ip-over-limit@example.com", None)
    response = await client.get("/auth/code", params={"email": "ip-over-limit@example.com"})
    assert response.status_code == 429
    assert "当前网络验证码请求过于频繁" in response.json()["detail"]
    assert int(fake_redis.values[f"{IP_LIMIT_PREFIX}:127.0.0.1"]) == 21


async def test_membership_recharge_and_transactions(client, session_maker):
    user = await create_user(session_maker)
    plan = await create_plan(session_maker, credits=30)

    me_response = await client.get("/membership/me", headers=auth_headers(user.id))
    assert me_response.status_code == 200
    assert me_response.json()["credit_balance"] == DEFAULT_FREE_CREDITS

    recharge_response = await client.post(
        "/membership/recharge",
        json={"plan_id": plan.id, "provider": "mock"},
        headers=auth_headers(user.id),
    )
    assert recharge_response.status_code == 200
    assert recharge_response.json()["credits"] == 30
    assert recharge_response.json()["status"] == "pending"
    assert recharge_response.json()["provider"] == "alipay"
    payload = json.loads(recharge_response.json()["payment_payload"])
    assert payload["provider"] == "alipay"
    assert "openapi-sandbox" in payload["checkout_url"]

    async with session_maker() as session:
        account = await session.scalar(select(UserMembership).where(UserMembership.user_id == user.id))
        assert account.credit_balance == DEFAULT_FREE_CREDITS

    mock_pay_response = await client.post(
        f"/membership/orders/{recharge_response.json()['id']}/mock-pay",
        headers=auth_headers(user.id),
    )
    assert mock_pay_response.status_code == 410

    pay_response = await client.post(
        f"/membership/orders/{recharge_response.json()['id']}/alipay-query",
        headers=auth_headers(user.id),
    )
    assert pay_response.status_code == 200
    assert pay_response.json()["status"] == "paid"

    transactions_response = await client.get("/membership/transactions", headers=auth_headers(user.id))
    assert transactions_response.status_code == 200
    transaction_types = {item["transaction_type"] for item in transactions_response.json()["items"]}
    assert {"grant", "recharge"} <= transaction_types

    async with session_maker() as session:
        account = await session.scalar(select(UserMembership).where(UserMembership.user_id == user.id))
        recharge = await session.scalar(
            select(CreditTransaction).where(CreditTransaction.transaction_type == "recharge")
        )
        order = await session.scalar(select(RechargeOrder).where(RechargeOrder.id == recharge_response.json()["id"]))
        assert account.credit_balance == DEFAULT_FREE_CREDITS + 30
        assert recharge.balance_after == DEFAULT_FREE_CREDITS + 30
        assert order.status == "paid"
        assert order.provider == "alipay"


async def test_membership_payment_notify_failure_and_refund(client, session_maker):
    user = await create_user(session_maker, email="pay@example.com")
    admin = await create_user(session_maker, email="admin-pay@example.com", is_admin=True)
    plan = await create_plan(session_maker, credits=15)

    paid_order_response = await client.post(
        "/membership/recharge",
        json={"plan_id": plan.id, "pay_scene": "wap"},
        headers=auth_headers(user.id),
    )
    assert paid_order_response.status_code == 200

    paid_notify_response = await client.post(
        "/membership/payment/notify/alipay",
        data={
            "out_trade_no": str(paid_order_response.json()["id"]),
            "trade_no": "ali-paid-1",
            "trade_status": "TRADE_SUCCESS",
            "sign": "valid",
        },
    )
    assert paid_notify_response.status_code == 200
    assert paid_notify_response.text == "success"

    duplicate_notify_response = await client.post(
        "/membership/payment/notify/alipay",
        data={
            "out_trade_no": str(paid_order_response.json()["id"]),
            "trade_no": "ali-paid-1",
            "trade_status": "TRADE_SUCCESS",
            "sign": "valid",
        },
    )
    assert duplicate_notify_response.status_code == 200
    assert duplicate_notify_response.text == "success"

    refund_response = await client.post(
        f"/admin/membership/orders/{paid_order_response.json()['id']}/refund",
        json={"reason": "test refund"},
        headers=auth_headers(admin.id),
    )
    assert refund_response.status_code == 200
    assert refund_response.json()["status"] == "refunded"

    async with session_maker() as session:
        account = await session.scalar(select(UserMembership).where(UserMembership.user_id == user.id))
        assert account.credit_balance == DEFAULT_FREE_CREDITS
        recharge_count = await session.scalar(
            select(func.count()).select_from(CreditTransaction).where(CreditTransaction.transaction_type == "recharge")
        )
        assert recharge_count == 1


async def test_paid_order_rolls_back_when_crediting_fails(client, session_maker, monkeypatch):
    user = await create_user(session_maker, email="rollback-pay@example.com")
    plan = await create_plan(session_maker, credits=12)

    recharge_response = await client.post(
        "/membership/recharge",
        json={"plan_id": plan.id},
        headers=auth_headers(user.id),
    )
    assert recharge_response.status_code == 200
    order_id = recharge_response.json()["id"]

    def fail_credit(self, order, account):
        raise RuntimeError("simulated credit failure")

    monkeypatch.setattr("core.membership_service.MembershipService._credit_paid_order", fail_credit)
    pay_response = await client.post(
        f"/membership/orders/{order_id}/alipay-query",
        headers=auth_headers(user.id),
    )
    assert pay_response.status_code == 500

    async with session_maker() as session:
        account = await session.scalar(select(UserMembership).where(UserMembership.user_id == user.id))
        order = await session.scalar(select(RechargeOrder).where(RechargeOrder.id == order_id))
        recharge_count = await session.scalar(
            select(func.count()).select_from(CreditTransaction).where(CreditTransaction.transaction_type == "recharge")
        )
        assert account.credit_balance == DEFAULT_FREE_CREDITS
        assert order.status == "pending"
        assert recharge_count == 0

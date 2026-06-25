import os
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ.setdefault("DB_URI", "mysql+aiomysql://test:test@127.0.0.1:3306/test")
os.environ.setdefault("DB_URI1", "mysql+aiomysql://test:test@127.0.0.1:3306/test")
os.environ.setdefault("LANGGRAPH_DB_URI", "postgresql://test:test@127.0.0.1:5432/test")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-for-pytest-only-32-bytes")

from core.auth import AuthHandler
from core.redisconfig import get_redis_client
from dependencies import get_email, get_session
from models import Base
from models.membership import MembershipPlan
from models.user import User
from routers import admin_router, auth_router, history_router, membership_router, name_router, preference_template_router, project_router, rag_router, user_router


class FakeMail:
    def __init__(self):
        self.messages = []

    async def send_message(self, message):
        self.messages.append(message)


class FakeRedis:
    def __init__(self):
        self.values = {}

    async def set(self, key, value, ex=None, nx=False):
        if nx and str(key) in self.values:
            return None
        self.values[str(key)] = value
        return True

    async def get(self, key):
        return self.values.get(str(key))

    async def delete(self, key):
        self.values.pop(str(key), None)
        return 1

    async def incr(self, key):
        key = str(key)
        value = int(self.values.get(key, 0)) + 1
        self.values[key] = str(value)
        return value

    async def expire(self, key, seconds):
        return True


@pytest.fixture
def fake_mail() -> FakeMail:
    return FakeMail()


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
async def session_maker(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(bind=engine, autoflush=True, expire_on_commit=False)
    try:
        yield maker
    finally:
        await engine.dispose()


@pytest.fixture
async def client(session_maker, fake_mail, fake_redis) -> AsyncGenerator[AsyncClient, None]:
    app = FastAPI()
    app.include_router(auth_router.router)
    app.include_router(user_router.router)
    app.include_router(membership_router.router)
    app.include_router(name_router.router)
    app.include_router(history_router.router)
    app.include_router(project_router.router)
    app.include_router(preference_template_router.router)
    app.include_router(rag_router.router)
    app.include_router(admin_router.router)

    async def override_get_session():
        async with session_maker() as session:
            yield session

    async def override_get_email():
        return fake_mail

    async def override_get_redis_client():
        yield fake_redis

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_email] = override_get_email
    app.dependency_overrides[get_redis_client] = override_get_redis_client

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()


def auth_headers(user_id: int) -> dict[str, str]:
    token = AuthHandler().encode_login_token(user_id)["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def create_user(session_maker, *, email: str = "user@example.com", is_admin: bool = False) -> User:
    async with session_maker() as session:
        username = email.split("@")[0]
        if len(username) < 4:
            username = f"{username}_user"
        user = User(email=email, username=username, password="password123", is_admin=is_admin)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def create_plan(
    session_maker,
    *,
    name: str = "Basic",
    price_cents: int = 990,
    credits: int = 20,
    is_active: bool = True,
) -> MembershipPlan:
    async with session_maker() as session:
        plan = MembershipPlan(
            name=name,
            description="Test plan",
            price_cents=price_cents,
            credits=credits,
            validity_days=30,
            is_active=is_active,
        )
        session.add(plan)
        await session.commit()
        await session.refresh(plan)
        return plan

from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status
from redis.asyncio.client import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from repository.user_repo import EmailCodeRepository
from settings import (
    EMAIL_CODE_EMAIL_COOLDOWN_SECONDS,
    EMAIL_CODE_EMAIL_HOURLY_LIMIT,
    EMAIL_CODE_IP_HOURLY_LIMIT,
    TRUST_PROXY_HEADERS,
)


EMAIL_LIMIT_PREFIX = "email_code:rate:email"
IP_LIMIT_PREFIX = "email_code:rate:ip"
COOLDOWN_PREFIX = "email_code:cooldown"
WINDOW_SECONDS = 3600


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if TRUST_PROXY_HEADERS and forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


async def _increment_window(redis: Redis, key: str, seconds: int) -> int:
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, seconds)
    return int(count)


def _raise_rate_limit(message: str) -> None:
    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)


async def enforce_email_code_rate_limit(
    *,
    email: str,
    request: Request,
    redis: Redis,
    session: AsyncSession,
) -> None:
    normalized_email = email.lower()
    client_ip = get_client_ip(request)

    try:
        cooldown_key = f"{COOLDOWN_PREFIX}:{normalized_email}"
        is_first_request = await redis.set(
            cooldown_key,
            "1",
            ex=EMAIL_CODE_EMAIL_COOLDOWN_SECONDS,
            nx=True,
        )
        if not is_first_request:
            _raise_rate_limit(f"验证码发送太频繁，请 {EMAIL_CODE_EMAIL_COOLDOWN_SECONDS} 秒后再试")

        email_count = await _increment_window(
            redis,
            f"{EMAIL_LIMIT_PREFIX}:{normalized_email}",
            WINDOW_SECONDS,
        )
        if email_count > EMAIL_CODE_EMAIL_HOURLY_LIMIT:
            _raise_rate_limit("该邮箱验证码请求过于频繁，请稍后再试")

        ip_count = await _increment_window(redis, f"{IP_LIMIT_PREFIX}:{client_ip}", WINDOW_SECONDS)
        if ip_count > EMAIL_CODE_IP_HOURLY_LIMIT:
            _raise_rate_limit("当前网络验证码请求过于频繁，请稍后再试")
    except HTTPException:
        raise
    except RedisError:
        await _enforce_database_fallback(normalized_email, session)


async def _enforce_database_fallback(email: str, session: AsyncSession) -> None:
    repository = EmailCodeRepository(session=session)
    now = datetime.now()
    recent_count = await repository.count_email_codes_since(
        email,
        now - timedelta(seconds=EMAIL_CODE_EMAIL_COOLDOWN_SECONDS),
    )
    if recent_count:
        _raise_rate_limit(f"验证码发送太频繁，请 {EMAIL_CODE_EMAIL_COOLDOWN_SECONDS} 秒后再试")

    hourly_count = await repository.count_email_codes_since(email, now - timedelta(seconds=WINDOW_SECONDS))
    if hourly_count >= EMAIL_CODE_EMAIL_HOURLY_LIMIT:
        _raise_rate_limit("该邮箱验证码请求过于频繁，请稍后再试")

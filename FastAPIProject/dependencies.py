from core.mailtools import create_mail_instance
from fastapi import Depends, HTTPException
from fastapi_mail import FastMail
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_403_FORBIDDEN

async def get_email():
    return create_mail_instance()

from models import AsyncSessionFactory

async def get_session():
    session = AsyncSessionFactory()
    try:
        # yield 借出去 session，意味着，如果用完，再换回来
        yield session
    finally:
        await session.close()

from core.auth import AuthHandler
from models.user import User

auth_handler = AuthHandler()

async def require_admin(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await session.get(User, user_id)
    if not user or not user.is_admin:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user

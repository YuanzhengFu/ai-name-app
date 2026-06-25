from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from core.auth import AuthHandler
from core.redisconfig import get_redis_client
from dependencies import get_session
from models.security import LoginRecord
from redis.asyncio.client import Redis
from repository.user_repo import UserRepository
from routers.auth_router import delete_email_code, verify_email_code
from schemas.user_schemas import ChangeEmailIn, ChangePasswordIn, LoginRecordOut, UserSchema, UserUpdateIn

auth_handler = AuthHandler()
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserSchema)
async def get_my_profile(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = UserRepository(session)
    user = await repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/me", response_model=UserSchema)
async def update_my_profile(
    data: UserUpdateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = UserRepository(session)
    user = await repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    return await repo.update_username(user, data.username)


@router.post("/me/password")
async def change_my_password(
    data: ChangePasswordIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = UserRepository(session)
    user = await repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    if not user.check_password(data.old_password):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Old password is incorrect")

    await repo.update_password(user, data.new_password)
    return {"message": "Password updated successfully"}


@router.post("/me/email", response_model=UserSchema)
async def change_my_email(
    data: ChangeEmailIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis_client),
):
    repo = UserRepository(session)
    user = await repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    if not user.check_password(data.password):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Password is incorrect")
    if await repo.email_is_exist(data.new_email):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Email already exists")

    await verify_email_code(str(data.new_email), data.code, session, redis)
    updated_user = await repo.update_email(user, str(data.new_email))
    await delete_email_code(str(data.new_email), redis)
    return updated_user


@router.get("/me/login-records", response_model=list[LoginRecordOut])
async def get_my_login_records(
    limit: int = 10,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    safe_limit = min(max(limit, 1), 50)
    result = await session.execute(
        select(LoginRecord)
        .where(LoginRecord.user_id == user_id)
        .order_by(LoginRecord.created_time.desc(), LoginRecord.id.desc())
        .limit(safe_limit)
    )
    return list(result.scalars().all())

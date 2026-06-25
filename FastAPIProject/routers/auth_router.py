import random
import string
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.params import Query
from fastapi_mail import MessageSchema, MessageType
from pydantic import EmailStr
from fastapi_mail import FastMail

router = APIRouter(prefix="/auth", tags=["auth"])
# 发送验证码给用户
from dependencies import get_email,get_session
from repository.user_repo import EmailCodeRepository
from sqlalchemy.ext.asyncio.session import AsyncSession

# EmailStr 是pydantic专门用来校验数据格式是否是邮箱的类
from core.redisconfig import get_redis_client
from core.email_rate_limit import enforce_email_code_rate_limit
from settings import EMAIL_CODE_TTL_SECONDS

from redis.asyncio.client import Redis
from redis.exceptions import RedisError
# 发送验证码的本质是做两件事：1.发送一个验证码给用户
#                         2.保存这个验证码到数据库
@router.get("/code")
async def get_email_code(email: Annotated[EmailStr,Query(...)],
                         request: Request,
                         fastmail:FastMail=Depends(get_email),
                         session:AsyncSession=Depends(get_session),
                         redis:Redis=Depends(get_redis_client)):
    await enforce_email_code_rate_limit(
        email=str(email),
        request=request,
        redis=redis,
        session=session,
    )
    # 1.生成验证码  digits = '0123456789'
    #  4位数的验证码  0123456789012345678901234567890123456789
    source = string.digits*4
    # sample的意思是从source这个字符串随机取4位数
    # sample的返回值是一个list，我们需要的验证码是一个字符串
    # code 就是我们生成的验证码
    code = "".join(random.sample(source,4))
    # 2.创建一个邮件  系统把邮件发给谁
    message = MessageSchema(
        subject="【ai起名字app】注册验证码",
        recipients=[email],
        body=f"您的验证码是：{code},五分钟内有效，请及时注册账号",
        subtype=MessageType.plain
    )
    # 3.发送邮件
    await fastmail.send_message(message)
    # 4.把发送的邮件信息保存起来
    email_repository = EmailCodeRepository(session=session)
    # redis存储的key和value，key是我们设计的，所以，取值的时候，也要用同样的规则
    try:
        await redis.set(str(email),code,ex=EMAIL_CODE_TTL_SECONDS)
    except RedisError:
        await email_repository.create_email_code(str(email),code)

    return {"message":"验证码发送成功"}

from schemas.user_schemas import RegisterIn,UserCreateSchema,LoginIn, ResetPasswordIn
from repository.user_repo import UserRepository
from core.membership_service import MembershipService


# 功能：用户注册。用户注册的本质是向用户表插入一条数据
#  用户在页面上填写自己的信息：用户名，密码，性别，邮箱等等。
#  后台要接收用户的信息。可以设计对象来接收，把接收对象转成数据库对象，存入数据库
@router.post("/register")
async def register(userinfo:RegisterIn,session:AsyncSession=Depends(get_session),redis:Redis=Depends(get_redis_client)):
    # 向用户表插入数据
    userRepository = UserRepository(session=session)
    # 用户传过来的信息中需要一些校验
    # 1.邮箱是否已经别别人注册了  该邮箱已注册，请直接登录
    email_exist = await userRepository.email_is_exist(userinfo.email)
    if email_exist:
        raise HTTPException(status_code=400,detail="该邮箱已经注册，请直接登录")
    # 2.看验证码是否正确，如果不对，不允许注册
    # emailCodeRepository = EmailCodeRepository(session=session)
    # email_code_bool = await emailCodeRepository.check_email_code(userinfo.email,userinfo.code)
    # key是email
    try:
        email_code = await redis.get(userinfo.email)
    except RedisError:
        emailCodeRepository = EmailCodeRepository(session=session)
        email_code_bool = await emailCodeRepository.check_email_code(userinfo.email,userinfo.code)
        if not email_code_bool:
            raise HTTPException(400, detail="验证码错误或者已过期")
        email_code = userinfo.code
    if (not email_code) or (userinfo.code != email_code):
        raise HTTPException(400, detail="验证码错误或者已过期")
    # 3.允许注册  插入一条数据到数据库
    userCreatSchema = UserCreateSchema(email=userinfo.email, username=userinfo.username, password=userinfo.password)
    user = await userRepository.create_user(userCreatSchema)
    await MembershipService(session).get_or_create_account(user.id)

    # 注册成功，删除redis中的数据
    try:
        await redis.delete(userinfo.email)
    except RedisError:
        pass
    return {"message":"恭喜您注册成功"}

from models.user import User
from models.security import LoginRecord
from core.auth import AuthHandler
from schemas.user_schemas import LoginOut
authHandler = AuthHandler()


async def verify_email_code(email: str, code: str, session: AsyncSession, redis: Redis) -> None:
    try:
        email_code = await redis.get(email)
    except RedisError:
        emailCodeRepository = EmailCodeRepository(session=session)
        email_code_bool = await emailCodeRepository.check_email_code(email, code)
        if not email_code_bool:
            raise HTTPException(400, detail="楠岃瘉鐮侀敊璇垨鑰呭凡杩囨湡")
        return
    if (not email_code) or (code != email_code):
        raise HTTPException(400, detail="楠岃瘉鐮侀敊璇垨鑰呭凡杩囨湡")


async def delete_email_code(email: str, redis: Redis) -> None:
    try:
        await redis.delete(email)
    except RedisError:
        pass


async def create_login_record(
    session: AsyncSession,
    request: Request,
    email: str,
    user_id: int | None,
    success: bool,
    failure_reason: str | None = None,
) -> None:
    session.add(
        LoginRecord(
            user_id=user_id,
            email=email,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=success,
            failure_reason=failure_reason,
        )
    )
    await session.commit()

@router.post("/login", response_model=LoginOut)
async def login(userinfo:LoginIn, request: Request, session:AsyncSession=Depends(get_session)):
    # 获取你的信息，邮箱，根据有想才能知道你是不是我们的会员
    # 1. 因为你想登录，我们得确定你是已经注册的用户，未注册的不让登陆
    userRepository = UserRepository(session=session)
    # 数据库查询
    user:User|None = await  userRepository.get_user_by_email(userinfo.email)
    if not user:
        await create_login_record(session, request, str(userinfo.email), None, False, "user_not_found")
        raise HTTPException(status_code=400,detail="该用户不存在！")
    # 2.看密码对不对，密码错误不让登陆
    if not user.check_password(userinfo.password):
        await create_login_record(session, request, str(userinfo.email), user.id, False, "invalid_password")
        raise HTTPException(status_code=400, detail="密码输入错误，请核对后输入！")
    # 3.密码正确，允许登录。登录的方法是，给用户返回一个令牌。用户拿着这个令牌，下次来证明是登录过了。
    auth_handler = AuthHandler()
    tokens = auth_handler.encode_login_token(user.id)
    await create_login_record(session, request, str(userinfo.email), user.id, True)
    return {
        "user": user,
        "token": tokens['access_token']
    }


@router.post("/password/reset")
async def reset_password(
    data: ResetPasswordIn,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis_client),
):
    userRepository = UserRepository(session=session)
    user = await userRepository.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await verify_email_code(str(data.email), data.code, session, redis)
    await userRepository.update_password(user, data.new_password)
    await delete_email_code(str(data.email), redis)
    return {"message": "Password reset successfully"}

from sqlalchemy.ext.asyncio.session import AsyncSession
from models.user import User, EmailCode
from sqlalchemy import func, select, exists
from datetime import datetime, timedelta

from schemas.user_schemas import UserCreateSchema


# 与email表交互的一个对象
class EmailCodeRepository():

    def __init__(self,session: AsyncSession):
       self.session = session

    # 写入操作：移除begin()，直接add + commit
    async def create_email_code(self, email: str, code: str):
        async with self.session.begin():  # ✅ 这才是异步SQLAlchemy的正确写法
            email_code = EmailCode(email=email, code=code)
            self.session.add(email_code)
        return email_code

    # 查询操作：保持不变
    async def check_email_code(self,email:str,code:str):
        email_code = await self.session.scalar(
            select(EmailCode).filter(EmailCode.email==email, EmailCode.code==code)
        )
        if not email_code:
            return False
        if (datetime.now() - email_code.created_time) >= timedelta(minutes=5):
            return False
        return True

    async def count_email_codes_since(self, email: str, since: datetime):
        return await self.session.scalar(
            select(func.count()).select_from(EmailCode).where(
                EmailCode.email == email,
                EmailCode.created_time >= since,
            )
        )

# 与user表交互的对象
class UserRepository():
    def __init__(self,session: AsyncSession):
        self.session = session

    # 查询操作：保持不变
    async def get_user_by_email(self,email:str):
        result = await self.session.execute(select(User).where(User.email==email))
        return result.scalar_one_or_none()

    # 写入操作：移除begin()，直接add + commit
    async def create_user(self,user:UserCreateSchema):
        user = User(**user.model_dump())
        self.session.add(user)
        await self.session.commit()  # 手动提交事务
        return user

    # 查询操作：保持不变
    async def get_user_by_id(self, user_id: int):
        return await self.session.get(User, user_id)

    async def update_username(self, user: User, username: str):
        user.username = username
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_password(self, user: User, password: str):
        user.password = password
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_email(self, user: User, email: str):
        user.email = email
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def email_is_exist(self, email: str):
        result = await self.session.execute(
            select(exists().where(User.email == email))
        )
        return result.scalar()

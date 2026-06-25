from typing import Annotated
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

# 接收用户传过来的数据的一个对象
RawPasswordStr = Annotated[str,Field(...,min_length=4,max_length=50)]
RawUserNameStr =Annotated[str,Field(...,min_length=4,max_length=50)]
class RegisterIn(BaseModel):
    email:EmailStr
    username:RawUserNameStr
    password:RawPasswordStr
    confirm_password:RawPasswordStr
    # 验证用户的有效性
    code:Annotated[str,Field(...,min_length=4,max_length=4)]

    # 完成确认密码的校验
    @model_validator(mode="after")
    def password_is_valid(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self

# 存入数据库的是少数字段
class UserCreateSchema(BaseModel):
    email:EmailStr
    username:RawUserNameStr
    password:RawPasswordStr
    is_admin: bool = False

# 开发对象，接收用户登录信息
class LoginIn(BaseModel):
    email:EmailStr
    password:RawPasswordStr

class UserSchema(BaseModel):
    id:Annotated[int,Field(...)]
    username: RawUserNameStr
    email: EmailStr
    is_admin: bool = False

class UserUpdateIn(BaseModel):
    username: RawUserNameStr

class ChangePasswordIn(BaseModel):
    old_password: RawPasswordStr
    new_password: RawPasswordStr
    confirm_password: RawPasswordStr

    @model_validator(mode="after")
    def password_is_valid(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self

class ResetPasswordIn(BaseModel):
    email: EmailStr
    code: Annotated[str, Field(..., min_length=4, max_length=4)]
    new_password: RawPasswordStr
    confirm_password: RawPasswordStr

    @model_validator(mode="after")
    def password_is_valid(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self

class ChangeEmailIn(BaseModel):
    new_email: EmailStr
    code: Annotated[str, Field(..., min_length=4, max_length=4)]
    password: RawPasswordStr

class LoginRecordOut(BaseModel):
    id: int
    email: EmailStr
    ip_address: str | None = None
    user_agent: str | None = None
    success: bool
    failure_reason: str | None = None
    created_time: datetime

class LoginOut(BaseModel):
    user:UserSchema
    token: str

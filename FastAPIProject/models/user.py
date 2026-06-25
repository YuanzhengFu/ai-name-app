from . import Base
from sqlalchemy import Boolean, Integer, String, DateTime
from sqlalchemy.orm import Mapped,mapped_column
from pwdlib import PasswordHash
from datetime import datetime

password_hash = PasswordHash.recommended()
class User(Base):
    __tablename__ = "user"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email:Mapped[str] = mapped_column(String(100),unique=True)
    username:Mapped[str] = mapped_column(String(100))
    is_admin:Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_time:Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    # 数据库中存储的是加密后的密码，不是明文  123456 dsfgsdgtuaseffgasgsd
    _password:Mapped[str] = mapped_column(String(200))

    # 1.校验数据：密码是否正确
    # *args 能够接受任意多个不带名字的参数  列表
    # **wargs 能够接受任意多个带名字的参数  字典
    def __init__(self,*args,**kwargs):
        password = kwargs.pop("password",None)
        super().__init__(*args,**kwargs)
        if password:
            # 增加了一个变量 password  设置password，会自动调用@password.setter
            self.password = password
    # 获取密码（返回加密后的字符串）
    @property
    def password(self):
        return self._password
    # 设置password 自动加密 默认调用
    @password.setter
    def password(self,password):
        self._password = password_hash.hash(password)
    # 校验密码  你登录淘宝，随便输入一个秘密，它会报告，密码错误。
    def check_password(self,password):
        return password_hash.verify(password,self._password)

class EmailCode(Base):
    __tablename__ = "email_code"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email:Mapped[str] = mapped_column(String(100))
    code:Mapped[str] = mapped_column(String(100))
    # 发送的验证码有时效性
    created_time:Mapped[datetime] = mapped_column(DateTime,default=datetime.now)

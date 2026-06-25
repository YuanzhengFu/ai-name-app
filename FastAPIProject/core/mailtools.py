from fastapi_mail import FastMail, ConnectionConfig
from pydantic import SecretStr, EmailStr
import settings

# 创建并返回邮件实例
def create_mail_instance():
    # 邮件连接配置（相当于登录邮箱的配置）
    config = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,    # 发件邮箱
        MAIL_PASSWORD=settings.MAIL_PASSWORD,    # 邮箱授权码
        MAIL_FROM=settings.MAIL_FROM,            # 发件邮箱（和上面一样）
        MAIL_PORT=settings.MAIL_PORT,            # 端口 587 / 465
        MAIL_SERVER=settings.MAIL_SERVER,        # 邮箱服务器 smtp.qq.com / smtp.163.com
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,  # 发件人名称
        MAIL_STARTTLS=True,                      # 开启 TLS（587端口用这个）
        MAIL_SSL_TLS=False,                      # 关闭 SSL（465端口才开）
        USE_CREDENTIALS=True,                    # 使用账号密码登录
        VALIDATE_CERTS=True                      # 验证证书
    )
    # 返回一个可以发邮件的对象
    return FastMail(config)
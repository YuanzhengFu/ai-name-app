import os
from datetime import timedelta


DB_URI = os.getenv("DB_URI", "mysql+aiomysql://root:password@127.0.0.1:3306/ainame397?charset=utf8mb4")
DB_URI1 = os.getenv("DB_URI1", "postgresql+psycopg://postgres:password@127.0.0.1:5432/ainame")

MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME)
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.qq.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "ainameapp")
MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "true").lower() == "true"
MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "false").lower() == "true"

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_DAYS", "1")))
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30")))

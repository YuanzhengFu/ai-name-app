import os
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _path_env(name: str, default: Path) -> Path:
    raw_value = os.getenv(name)
    path = Path(raw_value) if raw_value else default
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


_load_dotenv()

DB_URI = _required_env("DB_URI")
DB_URI1 = _required_env("DB_URI1")
DEEPSEEK_API_KEY = _required_env("DEEPSEEK_API_KEY")
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME)
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.qq.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "ainameapp")
MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "true").lower() == "true"
MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "false").lower() == "true"

JWT_SECRET_KEY = _required_env("JWT_SECRET_KEY")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_DAYS", "1")))
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30")))

SQLALCHEMY_ECHO = _bool_env("SQLALCHEMY_ECHO")
CORS_ALLOW_ORIGINS = _csv_env("CORS_ALLOW_ORIGINS", "*")
TRUST_PROXY_HEADERS = _bool_env("TRUST_PROXY_HEADERS")

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
EMAIL_CODE_TTL_SECONDS = int(os.getenv("EMAIL_CODE_TTL_SECONDS", "300"))
EMAIL_CODE_EMAIL_COOLDOWN_SECONDS = int(os.getenv("EMAIL_CODE_EMAIL_COOLDOWN_SECONDS", "60"))
EMAIL_CODE_EMAIL_HOURLY_LIMIT = int(os.getenv("EMAIL_CODE_EMAIL_HOURLY_LIMIT", "5"))
EMAIL_CODE_IP_HOURLY_LIMIT = int(os.getenv("EMAIL_CODE_IP_HOURLY_LIMIT", "20"))
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:admin123@127.0.0.1:5672/")
RAG_QUEUE_NAME = os.getenv("RAG_QUEUE_NAME", "rag_document_queue")
LANGGRAPH_DB_URI = os.getenv("LANGGRAPH_DB_URI", "postgresql://postgres:password@127.0.0.1:5432/ainame397")

UPLOAD_DIR = _path_env("UPLOAD_DIR", BASE_DIR / "uploads")
CHROMA_RAG_DB_PATH = _path_env("CHROMA_RAG_DB_PATH", BASE_DIR / "chroma_rag_db")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
ALLOWED_KNOWLEDGE_EXTENSIONS = {item.lower() for item in _csv_env("ALLOWED_KNOWLEDGE_EXTENSIONS", ".txt,.pdf")}

PAYMENT_DEFAULT_PROVIDER = os.getenv("PAYMENT_DEFAULT_PROVIDER", "mock")
PAYMENT_PUBLIC_BASE_URL = os.getenv("PAYMENT_PUBLIC_BASE_URL", "")

WECHAT_PAY_APPID = os.getenv("WECHAT_PAY_APPID", "")
WECHAT_PAY_MCH_ID = os.getenv("WECHAT_PAY_MCH_ID", "")
WECHAT_PAY_API_V3_KEY = os.getenv("WECHAT_PAY_API_V3_KEY", "")
WECHAT_PAY_SERIAL_NO = os.getenv("WECHAT_PAY_SERIAL_NO", "")
WECHAT_PAY_PRIVATE_KEY_PATH = os.getenv("WECHAT_PAY_PRIVATE_KEY_PATH", "")

ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "")
ALIPAY_GATEWAY = os.getenv("ALIPAY_GATEWAY", "https://openapi.alipay.com/gateway.do")
ALIPAY_PRIVATE_KEY_PATH = os.getenv("ALIPAY_PRIVATE_KEY_PATH", "")
ALIPAY_PUBLIC_KEY_PATH = os.getenv("ALIPAY_PUBLIC_KEY_PATH", "")

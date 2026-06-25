from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class LoginRecord(Base):
    __tablename__ = "login_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(100), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, index=True)

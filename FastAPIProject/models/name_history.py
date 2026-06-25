from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class NameHistory(Base):
    __tablename__ = "name_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("naming_project.id"), index=True, nullable=True)
    thread_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(20), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    reference: Mapped[str] = mapped_column(Text, nullable=False)
    moral: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), default="", server_default="")
    domain_status: Mapped[str] = mapped_column(String(100), default="", server_default="")
    domain_checks: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    brand_warning: Mapped[str | None] = mapped_column(Text, nullable=True)
    pinyin: Mapped[str] = mapped_column(String(255), default="", server_default="")
    english_name: Mapped[str] = mapped_column(String(255), default="", server_default="")
    abbreviation: Mapped[str] = mapped_column(String(50), default="", server_default="")
    score_total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    rhythm_score: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    meaning_score: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    spread_score: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    domain_score: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    score_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    surname: Mapped[str] = mapped_column(String(100), default="", server_default="")
    gender: Mapped[str] = mapped_column(String(20), default="", server_default="")
    length: Mapped[str] = mapped_column(String(20), default="", server_default="")
    other: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclude: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", index=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

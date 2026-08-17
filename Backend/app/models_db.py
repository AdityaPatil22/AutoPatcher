"""SQLAlchemy database models."""

from datetime import date, datetime, timezone

from cryptography.fernet import Fernet
from sqlalchemy import BigInteger, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

import app.config as config
from app.db import Base

_fernet = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(config.FERNET_KEY.encode())
    return _fernet


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    repo_path: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    github_repo_owner: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    github_repo_name: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    llm_requests_today: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    llm_requests_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    llm_model: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    max_context_files: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def set_access_token(self, token: str) -> None:
        self.access_token_encrypted = _get_fernet().encrypt(token.encode()).decode()

    def get_access_token(self) -> str:
        return _get_fernet().decrypt(self.access_token_encrypted.encode()).decode()

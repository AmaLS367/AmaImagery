from __future__ import annotations
import uuid
from sqlalchemy import String, Text, func, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import TIMESTAMP
from app.infra.db import Base
from datetime import datetime as dt

from sqlalchemy.engine.url import make_url as _make_url
from app.config import settings as _settings
from sqlalchemy import JSON as _GENERIC_JSON

def _is_pg() -> bool:
    try:
        return _make_url(_settings.database_url).get_backend_name() == "postgresql"
    except Exception:
        return False

def _UUID():
    return UUID(as_uuid=True) if _is_pg() else String(36)

def _JSON():
    return JSONB if _is_pg() else _GENERIC_JSON

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(_UUID(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped["dt"] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped["dt"] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    settings: Mapped["UserSettings"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserSettings(Base):
    __tablename__ = "user_settings"
    user_id: Mapped[uuid.UUID] = mapped_column(_UUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    data: Mapped[dict] = mapped_column(_JSON(), default=dict)
    updated_at: Mapped["dt"] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="settings")

class Generation(Base):
    __tablename__ = "generations"
    id: Mapped[uuid.UUID] = mapped_column(_UUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(_UUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    prompt: Mapped[dict] = mapped_column(_JSON(), default=dict)   # prompt/negative_prompt
    params: Mapped[dict] = mapped_column(_JSON(), default=dict)   # width/height/steps/seed/model_id/...
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

Index("ix_generations_user_time", Generation.user_id, Generation.created_at.desc())

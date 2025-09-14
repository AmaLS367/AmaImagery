from __future__ import annotations
import uuid
from sqlalchemy import String, Text, func, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import TIMESTAMP
from app.db import Base
from datetime import datetime as dt

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped["dt"] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped["dt"] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    settings: Mapped["UserSettings"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserSettings(Base):
    __tablename__ = "user_settings"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped["dt"] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="settings")

class Generation(Base):
    __tablename__ = "generations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    prompt: Mapped[dict] = mapped_column(JSONB, default=dict)   # prompt/negative_prompt
    params: Mapped[dict] = mapped_column(JSONB, default=dict)   # width/height/steps/seed/model_id/...
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)

Index("ix_generations_user_time", Generation.user_id, Generation.created_at.desc())

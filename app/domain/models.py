from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, TIMESTAMP, Uuid

from app.infra.db import Base

# Helper for JSON type: uses JSONB on Postgres for performance/indexing, generic JSON elsewhere
JSON_TYPE = JSON().with_variant(postgresql.JSONB, "postgresql")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    # Role management
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    settings: Mapped[UserSettings] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    data: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="settings")


class Generation(Base):
    __tablename__ = "generations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Stores prompt and negative_prompt
    prompt: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)

    # Stores technical params: width, height, steps, seed, model_id, etc.
    params: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)

    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False, index=True)
    provider_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    provider_state: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)
    result: Mapped[dict] = mapped_column(JSON_TYPE, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


# Composite index for optimizing user history queries
Index("ix_generations_user_time", Generation.user_id, Generation.created_at.desc())

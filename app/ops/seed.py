from __future__ import annotations

import asyncio

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, normalize_email
from app.domain.models import User, UserSettings
from app.infra.db import AsyncSessionLocal

DEFAULT_SETTINGS = {"style": "realistic", "steps": 28, "size": 768, "negative": ""}


async def _run_seed_async() -> None:
    async with AsyncSessionLocal() as db:
        email = normalize_email("admin@example.com")
        username = "admin"
        user = (
            await db.execute(select(User).where(or_(User.email == email, User.username == username)))
        ).scalar_one_or_none()

        if user is None:
            user = User(
                email=email,
                username=username,
                password_hash=hash_password("admin123"),
            )
            db.add(user)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                user = (
                    await db.execute(select(User).where(or_(User.email == email, User.username == username)))
                ).scalar_one_or_none()

        if user is not None:
            settings_row = (
                await db.execute(select(UserSettings).where(UserSettings.user_id == user.id))
            ).scalar_one_or_none()
            if settings_row is None:
                db.add(UserSettings(user_id=user.id, data=DEFAULT_SETTINGS.copy()))
            await db.commit()

    print("[seed] ok")


def run_seed() -> None:
    asyncio.run(_run_seed_async())

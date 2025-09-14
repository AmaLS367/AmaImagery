# app/ops/seed.py
from __future__ import annotations
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from app.db import SessionLocal
from app.models import User, UserSettings
from app.security import normalize_email, hash_password

DEFAULT_SETTINGS = {"style": "anime", "steps": 28, "size": 768, "negative": ""}

def run_seed() -> None:
    db = SessionLocal()
    try:
        email = normalize_email("admin@example.com")
        username = "admin"

        # 1) найти по email ИЛИ username
        user = db.execute(
            select(User).where(or_(User.email == email, User.username == username))
        ).scalar_one_or_none()

        # 2) создать при отсутствии; если упали на уникальности — перечитать и жить дальше
        if not user:
            user = User(
                email=email,
                username=username,
                password_hash=hash_password("admin123"),
            )
            db.add(user)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                user = db.execute(
                    select(User).where(or_(User.email == email, User.username == username))
                ).scalar_one_or_none()

        # 3) настройки — идемпотентно по user_id
        if user is not None:
            us = db.execute(
                select(UserSettings).where(UserSettings.user_id == user.id)
            ).scalar_one_or_none()
            if not us:
                us = UserSettings(user_id=user.id, data=DEFAULT_SETTINGS.copy())
                db.add(us)
            db.commit()

        print("[seed] ok")
    finally:
        db.close()

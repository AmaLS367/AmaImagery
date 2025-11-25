from __future__ import annotations
import subprocess
import sys
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_dev_migrations() -> None:
    backend = make_url(settings.database_url).get_backend_name()
    if backend not in ("postgresql", "postgresql+psycopg", "postgresql+psycopg2"):
        raise RuntimeError("Only PostgreSQL is supported for dev. Set DATABASE_URL to Postgres.")
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Alembic failed: {r.stdout}\n{r.stderr}")


"""Alembic migrations environment configuration."""

import logging
import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.infra.db import Base as RuntimeBase

# Configure logging programmatically instead of using alembic.ini
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)-5.5s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("alembic").setLevel(logging.INFO)

config = context.config

DATABASE_URL: str | None = None
try:
    from app.config import settings

    DATABASE_URL = settings.database_url
except Exception:
    DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set. Set it via environment variable or .env file")

config.set_main_option("sqlalchemy.url", DATABASE_URL)
target_metadata = RuntimeBase.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

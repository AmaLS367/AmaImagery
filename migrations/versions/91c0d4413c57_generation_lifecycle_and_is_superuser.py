"""generation lifecycle and is_superuser

Revision ID: 91c0d4413c57
Revises: b4655aadfa03
Create Date: 2026-03-10 11:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "91c0d4413c57"
down_revision: Union[str, Sequence[str], None] = "b4655aadfa03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    generation_columns = {column["name"] for column in inspector.get_columns("generations")}
    generation_indexes = {index["name"] for index in inspector.get_indexes("generations")}

    if "is_superuser" not in user_columns:
        op.add_column("users", sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()))

    if "status" not in generation_columns:
        op.add_column("generations", sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"))
    if "provider_name" not in generation_columns:
        op.add_column("generations", sa.Column("provider_name", sa.String(length=64), nullable=True))
    if "provider_job_id" not in generation_columns:
        op.add_column("generations", sa.Column("provider_job_id", sa.String(length=255), nullable=True))
    if "provider_state" not in generation_columns:
        op.add_column(
            "generations", sa.Column("provider_state", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb"))
        )
    if "result" not in generation_columns:
        op.add_column("generations", sa.Column("result", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")))
    if "error" not in generation_columns:
        op.add_column("generations", sa.Column("error", sa.Text(), nullable=True))
    if "started_at" not in generation_columns:
        op.add_column("generations", sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True))
    if "completed_at" not in generation_columns:
        op.add_column("generations", sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True))
    if "updated_at" not in generation_columns:
        op.add_column(
            "generations",
            sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    image_path_column = next(
        (column for column in inspector.get_columns("generations") if column["name"] == "image_path"), None
    )
    if image_path_column is not None and image_path_column.get("nullable", True) is False:
        op.alter_column("generations", "image_path", existing_type=sa.Text(), nullable=True)

    if "ix_generations_status" not in generation_indexes:
        op.create_index("ix_generations_status", "generations", ["status"], unique=False)
    if "ix_generations_provider_job_id" not in generation_indexes:
        op.create_index("ix_generations_provider_job_id", "generations", ["provider_job_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_generations_provider_job_id", table_name="generations")
    op.drop_index("ix_generations_status", table_name="generations")

    op.alter_column("generations", "image_path", existing_type=sa.Text(), nullable=False)

    op.drop_column("generations", "updated_at")
    op.drop_column("generations", "completed_at")
    op.drop_column("generations", "started_at")
    op.drop_column("generations", "error")
    op.drop_column("generations", "result")
    op.drop_column("generations", "provider_state")
    op.drop_column("generations", "provider_job_id")
    op.drop_column("generations", "provider_name")
    op.drop_column("generations", "status")

    op.drop_column("users", "is_superuser")

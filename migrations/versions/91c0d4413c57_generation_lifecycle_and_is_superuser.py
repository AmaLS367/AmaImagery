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
    op.add_column("users", sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.add_column("generations", sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"))
    op.add_column("generations", sa.Column("provider_name", sa.String(length=64), nullable=True))
    op.add_column("generations", sa.Column("provider_job_id", sa.String(length=255), nullable=True))
    op.add_column("generations", sa.Column("provider_state", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("generations", sa.Column("result", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("generations", sa.Column("error", sa.Text(), nullable=True))
    op.add_column("generations", sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("generations", sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column(
        "generations",
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.alter_column("generations", "image_path", existing_type=sa.Text(), nullable=True)

    op.create_index("ix_generations_status", "generations", ["status"], unique=False)
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

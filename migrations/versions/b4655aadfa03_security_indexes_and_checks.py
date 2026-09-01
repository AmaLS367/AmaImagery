from alembic import op
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "b4655aadfa03"
down_revision: Union[str, Sequence[str], None] = "506057d97046"
branch_labels = None
depends_on = None


def upgrade():
    # users.email уникальность (регистронезависимо), если таблица существует
    op.execute("""
    DO $$
    BEGIN
      IF to_regclass('public.users') IS NOT NULL THEN
        CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_lower ON public.users (lower(email));
      END IF;
    END$$;
    """)

    # refresh_tokens.jti уникальный
    op.execute("""
    DO $$
    BEGIN
      IF to_regclass('public.refresh_tokens') IS NOT NULL THEN
        CREATE UNIQUE INDEX IF NOT EXISTS ix_refresh_tokens_jti ON public.refresh_tokens (jti);
      END IF;
    END$$;
    """)

    # частые фильтры: created_at
    op.execute("""
    DO $$
    BEGIN
      IF to_regclass('public.generations') IS NOT NULL THEN
        CREATE INDEX IF NOT EXISTS ix_generations_created_at ON public.generations (created_at DESC);
      END IF;
    END$$;
    """)

    # лимиты длин на уровне БД (idempotent через DO/EXCEPTION)
    op.execute("""
    DO $$
    BEGIN
      IF to_regclass('public.users') IS NOT NULL AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='users' AND column_name='email'
      ) THEN
        BEGIN
          ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_email_len_ck;
          ALTER TABLE public.users ADD CONSTRAINT users_email_len_ck CHECK (char_length(email) <= 255);
        EXCEPTION WHEN duplicate_object THEN
          NULL;
        END;
      END IF;

      IF to_regclass('public.generations') IS NOT NULL AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='generations' AND column_name='prompt'
      ) THEN
        BEGIN
          ALTER TABLE public.generations DROP CONSTRAINT IF EXISTS generations_prompt_len_ck;
          ALTER TABLE public.generations ADD CONSTRAINT generations_prompt_len_ck CHECK (
            -- нет ключа 'prompt' в JSONB — ограничение пропускаем
            (NOT (prompt ? 'prompt'))
            OR (
              jsonb_typeof(prompt->'prompt') = 'string'
              AND char_length(prompt->>'prompt') <= 2000
            )
          );
        EXCEPTION WHEN duplicate_object THEN
          NULL;
        END;
      END IF;
    END$$;
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_users_email_lower;")
    op.execute("DROP INDEX IF EXISTS ix_refresh_tokens_jti;")
    op.execute("DROP INDEX IF EXISTS ix_generations_created_at;")
    op.execute("ALTER TABLE IF EXISTS public.users DROP CONSTRAINT IF EXISTS users_email_len_ck;")
    op.execute("ALTER TABLE IF EXISTS public.generations DROP CONSTRAINT IF EXISTS generations_prompt_len_ck;")

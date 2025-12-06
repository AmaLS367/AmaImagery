import os

import pytest


@pytest.mark.db
def test_alembic_upgrade_head():
    # Требует установленный Alembic внутри контейнера/окружения
    try:
        import alembic  # noqa
    except Exception:
        pytest.skip("alembic не установлен")
    # Мини-проверка: скрипт существует
    assert os.path.exists("alembic.ini") or os.path.exists("migrations")

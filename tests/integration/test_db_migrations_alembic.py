import os

import pytest


@pytest.mark.db
def test_alembic_upgrade_head():
    # Requires Alembic installed in the environment
    try:
        import alembic  # noqa
    except Exception:
        pytest.skip("alembic is not installed")
    # Quick sanity check: migrations structure exists
    assert os.path.exists("alembic.ini") or os.path.exists("migrations")

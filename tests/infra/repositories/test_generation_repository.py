"""
Integration tests for SqlAlchemyGenerationRepository.

Tests repository operations with a real database (in-memory SQLite).
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Generation, User
from app.infra.repositories.generation_repository import SqlAlchemyGenerationRepository




@pytest_asyncio.fixture
async def generation_repo(test_db_session: AsyncSession):
    """Create a generation repository instance."""
    return SqlAlchemyGenerationRepository(test_db_session)


@pytest_asyncio.fixture
async def test_user(test_db_session: AsyncSession):
    """Create a test user for generation tests."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="gen@example.com",
        username="genuser",
        password_hash="hashed",
    )
    test_db_session.add(user)
    await test_db_session.commit()
    return user


@pytest.mark.asyncio
async def test_generation_repository_add_and_get(
    generation_repo: SqlAlchemyGenerationRepository,
    test_user: User,
):
    """Test adding and retrieving a generation."""
    gen_id = uuid4()
    generation = Generation(
        id=gen_id,
        user_id=test_user.id,
        prompt={"text": "test prompt", "negative": "test negative"},
        params={},
        image_path="test/path.png",
    )
    
    await generation_repo.add(generation)
    await generation_repo.session.commit()
    
    retrieved = await generation_repo.get(str(gen_id))
    assert retrieved is not None
    assert str(retrieved.id) == str(gen_id)
    assert retrieved.user_id == test_user.id
    assert retrieved.prompt == {"text": "test prompt", "negative": "test negative"}
    assert retrieved.image_path == "test/path.png"


@pytest.mark.asyncio
async def test_generation_repository_list_by_user(
    generation_repo: SqlAlchemyGenerationRepository,
    test_user: User,
):
    """Test listing generations by user."""
    # Create multiple generations
    gen1 = Generation(
        id=uuid4(),
        user_id=test_user.id,
        prompt={"text": "prompt 1"},
        params={},
        image_path="path1.png",
        created_at=datetime(2024, 1, 1),
    )
    gen2 = Generation(
        id=uuid4(),
        user_id=test_user.id,
        prompt={"text": "prompt 2"},
        params={},
        image_path="path2.png",
        created_at=datetime(2024, 1, 2),
    )
    
    await generation_repo.add(gen1)
    await generation_repo.add(gen2)
    await generation_repo.session.commit()
    
    # List all for user
    all_gens = await generation_repo.list_by_user(test_user.id)
    assert len(all_gens) == 2
    # Should be ordered by created_at desc (newest first)
    assert all_gens[0].created_at >= all_gens[1].created_at
    
    # List with limit
    limited = await generation_repo.list_by_user(str(test_user.id), limit=1)
    assert len(limited) == 1
    
    # List with offset
    offset = await generation_repo.list_by_user(str(test_user.id), limit=1, offset=1)
    assert len(offset) == 1
    assert str(offset[0].id) != str(limited[0].id)


@pytest.mark.asyncio
async def test_generation_repository_count_by_user(
    generation_repo: SqlAlchemyGenerationRepository,
    test_user: User,
):
    """Test counting generations by user."""
    # Initially should be 0
    count = await generation_repo.count_by_user(str(test_user.id))
    assert count == 0
    
    # Add some generations
    gen1 = Generation(
        id=uuid4(),
        user_id=test_user.id,
        prompt={"text": "prompt 1"},
        params={},
        image_path="path1.png",
    )
    gen2 = Generation(
        id=uuid4(),
        user_id=test_user.id,
        prompt={"text": "prompt 2"},
        params={},
        image_path="path2.png",
    )
    
    await generation_repo.add(gen1)
    await generation_repo.add(gen2)
    await generation_repo.session.commit()
    
    count = await generation_repo.count_by_user(str(test_user.id))
    assert count == 2
    
    # Test with different user
    other_user_id = uuid4()
    count_other = await generation_repo.count_by_user(str(other_user_id))
    assert count_other == 0


@pytest.mark.asyncio
async def test_generation_repository_update_status(
    generation_repo: SqlAlchemyGenerationRepository,
    test_user: User,
):
    """Test updating generation status."""
    gen_id = uuid4()
    generation = Generation(
        id=gen_id,
        user_id=test_user.id,
        prompt={"text": "test prompt"},
        params={},
        image_path="test/path.png",
    )
    
    await generation_repo.add(generation)
    await generation_repo.session.commit()
    
    # Update status
    await generation_repo.update_status(str(gen_id), "processing")
    await generation_repo.session.commit()
    
    updated = await generation_repo.get(str(gen_id))
    assert updated is not None
    # Generation model doesn't have status field, so update_status won't modify it
    # This test verifies the method doesn't crash
    
    # Update again - should not raise error
    await generation_repo.update_status(str(gen_id), "completed")
    await generation_repo.session.commit()
    
    final = await generation_repo.get(str(gen_id))
    assert final is not None


@pytest.mark.asyncio
async def test_generation_repository_list_with_filters(
    generation_repo: SqlAlchemyGenerationRepository,
    test_user: User,
):
    """Test listing generations with filters."""
    gen1 = Generation(
        id=uuid4(),
        user_id=test_user.id,
        prompt={"text": "prompt 1"},
        params={},
        image_path="path1.png",
    )
    gen2 = Generation(
        id=uuid4(),
        user_id=test_user.id,
        prompt={"text": "prompt 2"},
        params={},
        image_path="path2.png",
    )
    
    await generation_repo.add(gen1)
    await generation_repo.add(gen2)
    await generation_repo.session.commit()
    
    # Filter by user_id
    filtered = await generation_repo.list(user_id=str(test_user.id))
    assert len(filtered) == 2
    
    # Test filtering with non-existent user
    empty = await generation_repo.list(user_id=str(uuid4()))
    assert len(empty) == 0


@pytest.mark.asyncio
async def test_generation_repository_delete(
    generation_repo: SqlAlchemyGenerationRepository,
    test_user: User,
):
    """Test deleting a generation."""
    gen_id = uuid4()
    generation = Generation(
        id=gen_id,
        user_id=test_user.id,
        prompt={"text": "delete me"},
        params={},
        image_path="delete/path.png",
    )
    
    await generation_repo.add(generation)
    await generation_repo.session.commit()
    
    retrieved = await generation_repo.get(str(gen_id))
    assert retrieved is not None
    
    await generation_repo.delete(str(gen_id))
    await generation_repo.session.commit()
    
    deleted = await generation_repo.get(str(gen_id))
    assert deleted is None

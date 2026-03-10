"""
Integration tests for SqlAlchemyUserRepository.

Tests repository operations with a real database (in-memory SQLite).
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User, UserSettings
from app.infra.repositories.user_repository import SqlAlchemyUserRepository




@pytest_asyncio.fixture
async def user_repo(test_db_session: AsyncSession):
    """Create a user repository instance."""
    return SqlAlchemyUserRepository(test_db_session)


@pytest.mark.asyncio
async def test_user_repository_add_and_get(user_repo: SqlAlchemyUserRepository):
    """Test adding and retrieving a user."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
    )
    
    await user_repo.add(user)
    await user_repo.session.commit()
    
    retrieved = await user_repo.get(str(user_id))
    assert retrieved is not None
    assert str(retrieved.id) == str(user_id)
    assert retrieved.email == "test@example.com"
    assert retrieved.username == "testuser"


@pytest.mark.asyncio
async def test_user_repository_get_by_email(user_repo: SqlAlchemyUserRepository):
    """Test retrieving user by email."""
    user = User(
        id=uuid4(),
        email="findme@example.com",
        username="findme",
        password_hash="hashed",
    )
    
    await user_repo.add(user)
    await user_repo.session.commit()
    
    found = await user_repo.get_by_email("findme@example.com")
    assert found is not None
    assert found.email == "findme@example.com"
    assert found.username == "findme"
    
    not_found = await user_repo.get_by_email("nonexistent@example.com")
    assert not_found is None


@pytest.mark.asyncio
async def test_user_repository_get_by_username(user_repo: SqlAlchemyUserRepository):
    """Test retrieving user by username."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        username="unique_username",
        password_hash="hashed",
    )
    
    await user_repo.add(user)
    await user_repo.session.commit()
    
    found = await user_repo.get_by_username("unique_username")
    assert found is not None
    assert found.username == "unique_username"
    
    not_found = await user_repo.get_by_username("nonexistent")
    assert not_found is None


@pytest.mark.asyncio
async def test_user_repository_get_by_email_or_username(user_repo: SqlAlchemyUserRepository):
    """Test retrieving user by email or username."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="either@example.com",
        username="either_user",
        password_hash="hashed",
    )
    
    await user_repo.add(user)
    await user_repo.session.commit()
    
    found_by_email = await user_repo.get_by_email_or_username("either@example.com", "other")
    assert found_by_email is not None
    assert found_by_email.email == "either@example.com"
    
    found_by_username = await user_repo.get_by_email_or_username("other@example.com", "either_user")
    assert found_by_username is not None
    assert found_by_username.username == "either_user"
    
    not_found = await user_repo.get_by_email_or_username("nonexistent@example.com", "nonexistent")
    assert not_found is None


@pytest.mark.asyncio
async def test_user_repository_list_with_filters(user_repo: SqlAlchemyUserRepository):
    """Test listing users with filters."""
    user1 = User(
        id=uuid4(),
        email="user1@example.com",
        username="user1",
        password_hash="hashed",
    )
    user2 = User(
        id=uuid4(),
        email="user2@example.com",
        username="user2",
        password_hash="hashed",
    )
    
    await user_repo.add(user1)
    await user_repo.add(user2)
    await user_repo.session.commit()
    
    all_users = await user_repo.list()
    assert len(all_users) >= 2
    
    filtered = await user_repo.list(email="user1@example.com")
    assert len(filtered) == 1
    assert filtered[0].email == "user1@example.com"


@pytest.mark.asyncio
async def test_user_repository_delete(user_repo: SqlAlchemyUserRepository):
    """Test deleting a user."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="delete@example.com",
        username="delete",
        password_hash="hashed",
    )
    
    await user_repo.add(user)
    await user_repo.session.commit()
    
    retrieved = await user_repo.get(str(user_id))
    assert retrieved is not None
    
    await user_repo.delete(str(user_id))
    await user_repo.session.commit()
    
    deleted = await user_repo.get(str(user_id))
    assert deleted is None


@pytest.mark.asyncio
async def test_user_repository_get_settings(user_repo: SqlAlchemyUserRepository):
    """Test retrieving user settings."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="settings@example.com",
        username="settings",
        password_hash="hashed",
    )
    
    await user_repo.add(user)
    await user_repo.session.commit()
    
    settings = UserSettings(
        user_id=user_id,
        data={"nsfw_allow": True, "autocorrect": True},
    )
    
    await user_repo.save_settings(settings)
    await user_repo.session.commit()
    
    retrieved = await user_repo.get_settings(str(user_id))
    assert retrieved is not None
    assert str(retrieved.user_id) == str(user_id)
    assert retrieved.data.get("nsfw_allow") is True
    assert retrieved.data.get("autocorrect") is True


@pytest.mark.asyncio
async def test_user_repository_save_settings(user_repo: SqlAlchemyUserRepository):
    """Test saving user settings."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="save@example.com",
        username="save",
        password_hash="hashed",
    )
    
    await user_repo.add(user)
    await user_repo.session.commit()
    
    settings = UserSettings(
        user_id=user_id,
        data={"nsfw_allow": False, "autocorrect": False},
    )
    
    await user_repo.save_settings(settings)
    await user_repo.session.commit()
    
    retrieved = await user_repo.get_settings(str(user_id))
    assert retrieved is not None
    assert retrieved.data.get("nsfw_allow") is False
    assert retrieved.data.get("autocorrect") is False
    
    # Update settings
    retrieved.data["nsfw_allow"] = True
    await user_repo.save_settings(retrieved)
    await user_repo.session.commit()
    
    updated = await user_repo.get_settings(str(user_id))
    assert updated is not None
    assert updated.data.get("nsfw_allow") is True


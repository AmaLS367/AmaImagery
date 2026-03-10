import asyncio
from uuid import uuid4

from sqlalchemy import select

from app.domain.models import Generation, User
from app.infra.db import AsyncSessionLocal


def _register_and_login(app_client, *, email: str, username: str, password: str = "pass12345"):
    register = app_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "username": username},
    )
    assert register.status_code in (201, 409)
    login = app_client.post(
        "/api/v1/auth/login",
        json={"identifier": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return login


async def _mark_superuser(email: str) -> str:
    async with AsyncSessionLocal() as session:
        db_user = await session.scalar(select(User).where(User.email == email))
        if db_user is None:
            raise RuntimeError("User not found")
        db_user.is_superuser = True
        await session.commit()
        return db_user.id


async def _create_generation(user_id) -> str:
    async with AsyncSessionLocal() as session:
        generation = Generation(
            id=uuid4(),
            user_id=user_id,
            prompt={"prompt": "admin prompt"},
            params={"width": 512, "height": 512},
            status="completed",
            provider_name="comfyui",
            provider_job_id="prompt-admin-1",
            provider_state={"prompt_id": "prompt-admin-1"},
            result={"seed": 7},
            image_path="C:/outputs/admin.png",
        )
        session.add(generation)
        await session.commit()
        return str(generation.id)


def test_admin_requires_authentication(app_client):
    response = app_client.get("/admin/generations")

    assert response.status_code == 401


def test_admin_requires_superuser_role(app_client):
    _register_and_login(app_client, email="user@example.com", username="plain-user")

    response = app_client.get("/admin/generations")

    assert response.status_code == 403


def test_superuser_can_access_admin_pages(app_client):
    _register_and_login(app_client, email="admin@example.com", username="admin-user")
    user_id = asyncio.run(_mark_superuser("admin@example.com"))
    generation_id = asyncio.run(_create_generation(user_id))

    response = app_client.get("/admin/generations?status=completed&provider=comfyui")
    detail = app_client.get(f"/admin/generations/{generation_id}")
    users = app_client.get("/admin/users")

    assert response.status_code == 200
    assert "AmaImagery Admin" in response.text
    assert generation_id in response.text
    assert detail.status_code == 200
    assert "prompt-admin-1" in detail.text
    assert users.status_code == 200
    assert "admin@example.com" in users.text

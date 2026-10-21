from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import verify_password
from app.db.session import get_db_session
from app.models.user import User


async def register_user(client: AsyncClient, email: str = "user@example.com") -> dict[str, object]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strong-password",
            "full_name": "Example User",
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "fastapi-production-starter"}


async def test_user_registration(client: AsyncClient) -> None:
    payload = await register_user(client)

    assert payload["email"] == "user@example.com"
    assert payload["full_name"] == "Example User"
    assert "hashed_password" not in payload


async def test_duplicate_email_rejection(client: AsyncClient) -> None:
    await register_user(client)

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "strong-password",
            "full_name": "Another User",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_resource"


async def test_login_with_valid_credentials(client: AsyncClient) -> None:
    await register_user(client)

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "strong-password"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert isinstance(payload["access_token"], str)


async def test_login_failure_with_invalid_credentials(client: AsyncClient) -> None:
    await register_user(client)

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


async def test_authenticated_me(client: AsyncClient) -> None:
    await register_user(client)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "strong-password"},
    )
    token = login_response.json()["access_token"]

    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


async def test_unauthorized_me(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


async def test_password_is_stored_hashed(client: AsyncClient) -> None:
    await register_user(client)
    dependency = client._transport.app.dependency_overrides[get_db_session]

    async for session in dependency():
        result = await session.execute(select(User).where(User.email == "user@example.com"))
        user = result.scalar_one()
        assert user.hashed_password != "strong-password"
        assert verify_password("strong-password", user.hashed_password)
        break

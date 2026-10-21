from uuid import UUID

import jwt

from app.core.exceptions import DuplicateResourceError, InactiveUserError, InvalidCredentialsError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def register_user(self, user_create: UserCreate) -> User:
        existing_user = await self.user_repository.get_by_email(str(user_create.email))
        if existing_user is not None:
            raise DuplicateResourceError("A user with this email already exists")

        return await self.user_repository.create(
            email=str(user_create.email),
            hashed_password=hash_password(user_create.password),
            full_name=user_create.full_name,
        )

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.user_repository.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InactiveUserError()
        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.authenticate(email, password)
        return TokenResponse(access_token=create_access_token(user.id))

    async def get_current_user(self, token: str) -> User:
        try:
            payload = decode_access_token(token)
            subject = payload.get("sub")
            if not isinstance(subject, str):
                raise InvalidCredentialsError()
            user_id = UUID(subject)
        except (ValueError, jwt.InvalidTokenError) as exc:
            raise InvalidCredentialsError("Could not validate credentials") from exc

        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError("Could not validate credentials")
        if not user.is_active:
            raise InactiveUserError()
        return user

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_auth_service, get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin
from app.schemas.common import ErrorResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
    summary="Register a new user",
)
async def register(
    user_create: UserCreate,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    user = await auth_service.register_user(user_create)
    await session.commit()
    response.headers["Location"] = f"/api/v1/users/{user.id}"
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Authenticate and receive a bearer token",
)
async def login(
    credentials: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return await auth_service.login(str(credentials.email), credentials.password)


@router.get(
    "/me",
    response_model=UserRead,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Get the current authenticated user",
)
async def read_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user

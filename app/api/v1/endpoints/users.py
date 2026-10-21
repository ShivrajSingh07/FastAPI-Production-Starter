from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.schemas.user import UserRead

router = APIRouter()


@router.get(
    "/{user_id}",
    response_model=UserRead,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Get a user by ID",
    description="Allows an authenticated user to fetch their own public account details.",
)
async def read_user(
    user_id: UUID, current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if current_user.id != user_id:
        raise NotFoundError("User not found")
    return current_user




from uuid import UUID

from fastapi import APIRouter, Depends, status

from user_service.schemas.user import CreateUserRequest, User
from user_service.service.user import UserService, get_user_service


router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    request: CreateUserRequest,
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.create_user(request=request)


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
)
async def get_user_by_id(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.get_user_by_id(user_id=user_id)

@router.get(
    "/by-username/{username}", 
    status_code=status.HTTP_200_OK,
)
async def get_user_by_username(
    username: str,
    service: UserService = Depends(get_user_service),
) -> User:
    return await service.get_user_by_username(username=username)
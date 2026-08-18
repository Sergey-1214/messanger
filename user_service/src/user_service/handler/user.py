


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

from uuid import UUID

from fastapi import APIRouter, Depends, status

from user_service.handler.dependencies import VerifiedUserIdDep
from user_service.schemas.settings import Settings, SettingsUpdateRequest
from user_service.service.settings import SettingsService, get_settings_service


router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)

@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
)
async def get_settings(
    user_id: UUID,
    service: SettingsService = Depends(get_settings_service),
) -> Settings:
    return await service.get_settings(user_id=user_id)

@router.patch(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
)
async def update_settings(
    user_id: VerifiedUserIdDep,
    request: SettingsUpdateRequest,
    service: SettingsService = Depends(get_settings_service),
) -> Settings:
    return await service.update_settings(user_id=user_id, request=request)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_settings(
    user_id: VerifiedUserIdDep,
    service: SettingsService = Depends(get_settings_service),
) -> None:
    await service.clear_settings(user_id=user_id)